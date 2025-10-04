from collections import defaultdict
import logging

from app.api.filter.antlr.antlr_service import get_sql
from app.model.pydantic.filter import filter_schema, value_schema
from app.model.sqlalchemy.source_object_model import EntityTag
from app.services import config_service, exception_service
from app.services.acl import org_service
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

logger = logging.getLogger(__name__)

TAG_COLUMN_MAPPING = EntityTag.get_all_column_names()

def generate_entity_data(rs, tags):
    result = defaultdict(lambda: {"entity_id": None, "tags": []})
    if tags: 
        keys = ["entity_id"] + TAG_COLUMN_MAPPING
        for data in rs:
            tag_data = {key: value for key, value in zip(keys, data)}
            entity_id = tag_data['entity_id']
            
            if result[entity_id]["entity_id"] is None:
                result[entity_id]["entity_id"] = entity_id

            result[entity_id]["tags"].append(tag_data)
    else:
        for row in rs:
            result[row[0]]["entity_id"] = row[0]
    
    result = list(result.values())
    return result

def filter_objects(db, req_filter: filter_schema.FilterRequest, user: int):
    if org_service.is_org_visible_for_user(db, req_filter.org_id, user):
        tags = req_filter.tags
        try:
            sql = get_sql(req_filter.filter, tags, req_filter.org_id,
                        user, config_service.dbSchema)
            rs = db.execute(text(sql)).fetchall()
            return generate_entity_data(rs, tags)

        except ProgrammingError as e:
            error_message = str(e)
            if "column" in error_message and "does not exist" in error_message:
                missing_column = error_message.split("column ")[1].split(" ")[0]
                error_message = f"Invalid column name '{missing_column}'. Please correct the column name in the 'tags' list."
            raise HTTPException(status_code=500, detail=str(error_message))


    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op",
                                      type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )


def get_values(db, req_filter: value_schema.ValueRequest, user: int):
    result = []
    entities = filter_objects(db, req_filter, user)
    if req_filter.operation.aggregation != "" \
            and req_filter.operation.aggregation is not None \
            and req_filter.operation.timeInSeconds is not None:
        sql_template = get_aggregation_values_query()
    else:
        sql_template = get_values_query()
    entity_ids = ""
    value_table = ""
    for entity in entities:
        entity_ids += str(entity[0]) + ","
        value_table = entity[1]
    if entity_ids != "":
        entity_ids = entity_ids[:-1]
        sql = attach_query_variables(sql_template, req_filter, entity_ids, value_table)
        rs = db.execute(text(sql)).fetchall()
        for row in rs:
            result.append(row)
    return result


def get_variable_values(db, req_filter: filter_schema.FilterRequest, user: int):
    result = []
    entities = filter_objects(db, req_filter, user)
    sql_template = get_var_values_query()
    for entity in entities:
        sql = attach_vars_to_var_query(sql_template, req_filter, entity)
        rs = db.execute(text(sql))
        for row in rs:
            result.append(row._asdict())
    return result


def attach_tags_query_part(val_tag, query):
    if val_tag is None:
        val_tag = 'dis'

    tag_select_query_part_arr = []
    tag_select_table_part_arr = []
    tag_condition_query_part_arr = []
    val_tags = val_tag.split(',')
    for idx, tag in enumerate(val_tags):
        tag_num = idx + 10
        tag_select_query_part_arr.append('et' + str(tag_num) + '.value_s')
        tag_select_table_part_arr.append(
            config_service.dbSchema + '.tag_def td' + str(tag_num) + ','
            + config_service.dbSchema + '.entity_tag et' + str(tag_num) + ',')
        tag_condition_query_part_arr.append(
            ' and td' + str(tag_num) + '.name = \'' + tag + '\''
            + ' and td' + str(tag_num) + '.id = et' + str(tag_num) + '.tag_id'
            + ' and et' + str(tag_num) + '.entity_id = v.entity_id')

    tag_select_query_part = ' || \'||\'  || '.join(tag_select_query_part_arr)
    tag_select_table_part = ''.join(tag_select_table_part_arr)
    tag_condition_query_part = ''.join(tag_condition_query_part_arr)
    return query.replace("<tag_select_query_part>", tag_select_query_part) \
        .replace("<tag_select_table_part>", tag_select_table_part) \
        .replace("<tag_condition_query_part>", tag_condition_query_part)


def attach_query_variables(sql_template, req_filter, entity_ids, value_table):
    if req_filter.operation.aggregation != "" \
            and req_filter.operation.aggregation is not None \
            and req_filter.operation.timeInSeconds is not None:
        return attach_tags_query_part(req_filter.val_tag, sql_template) \
            .replace("<entity_id>", entity_ids) \
            .replace("<date_from>", req_filter.date_from) \
            .replace("<aggregation>", req_filter.operation.aggregation) \
            .replace("<time_in_seconds>", str(req_filter.operation.timeInSeconds)) \
            .replace("<date_to>", req_filter.date_to) \
            .replace("<value_table>", value_table)
    else:
        return attach_tags_query_part(req_filter.val_tag, sql_template) \
            .replace("<entity_id>", entity_ids) \
            .replace("<date_from>", req_filter.date_from) \
            .replace("<date_to>", req_filter.date_to) \
            .replace("<val_tag>", req_filter.val_tag) \
            .replace("<value_table>", value_table)


def attach_vars_to_var_query(sql_template, req_filter, entity):
    return sql_template.replace("<entity_id>", str(entity[0])) \
        .replace("<tag_name>", req_filter.tag)


def get_values_query():
    return """select v.*, et2.value_s kind, <tag_select_query_part> entity_name from {}.\"<value_table>\" v, <tag_select_table_part> {}.tag_def td2 , {}.entity_tag et2  
            where v.entity_id   in (<entity_id>) 
            <tag_condition_query_part>
            and td2.name = 'kind' 
            and td2.id = et2.tag_id 
            and et2.entity_id  = v.entity_id 
            and ts > '<date_from>'
            and ts < '<date_to>'
            limit 1000
            """.format(config_service.dbSchema, config_service.dbSchema, config_service.dbSchema,
                       config_service.dbSchema, config_service.dbSchema, config_service.dbSchema, config_service.dbSchema, config_service.dbSchema,
                       config_service.dbSchema, config_service.dbSchema)


def get_var_values_query():
    return """select et.tag_id, (case
            when (p.parent_ids ilike ',str%') THEN (et.value_s)
            when (p.parent_ids ilike ',number%') THEN (et.value_n)::text
            when (p.parent_ids ilike ',bool%') THEN (et.value_b)::text
            when (p.parent_ids ilike ',date%') THEN (et.value_ts)::text
            when (p.parent_ids ilike ',dict%') THEN (et.value_dict)::text
            when (p.parent_ids ilike ',enum%') THEN (et.value_enum)::text
            when (p.parent_ids ilike ',list%') THEN (et.value_list)::text
            when (p.parent_ids ilike ',ref%') THEN (et.value_ref)::text
            end) AS value
                from {}.tag_def tg
                left join {}.entity_tag et on et.tag_id = tg.id
                left join {}.tag_def_parents p on p.tag_id = tg.id
            where tg.name = '<tag_name>' and entity_id = <entity_id> limit 1000
            """.format(config_service.dbSchema, config_service.dbSchema, config_service.dbSchema)


def get_aggregation_values_query():
    return """select time_bucket_gapfill('<time_in_seconds> seconds', v.ts, '<date_from>', '<date_to>') as time,
                v.entity_id, v.status, et2.value_s kind, <tag_select_query_part> entity_name,
                locf(CASE WHEN (et2.value_s = 'Number') THEN (<aggregation>(v.value_n)) END) AS value_n
            from {}.\"<value_table>\" v, <tag_select_table_part> {}.tag_def td2 , {}.entity_tag et2 
            where v.entity_id  in (<entity_id>) 
                <tag_condition_query_part>
                and td2.name = 'kind'
                and td2.id = et2.tag_id
                and et2.entity_id  = v.entity_id
                and ts > '<date_from>'
                and ts < '<date_to>'
            group by (v.entity_id, v.status, kind, entity_name, time)
            limit 1000
                    """.format(config_service.dbSchema, config_service.dbSchema, config_service.dbSchema,
                               config_service.dbSchema, config_service.dbSchema)
