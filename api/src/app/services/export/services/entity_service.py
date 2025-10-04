import logging


logger = logging.getLogger(__name__)

def get_id_value_from_tags(tags):
    for tag in tags:
        if tag["tag_id"] == 342:
            return tag["value_s"]
    return None
def get_value(value):
    if str(value).startswith("'@"):
        return value[1:]
    return value
def isTagEnum(tag_id, enums):
    for enum in enums:
        if enums[enum]["tag_id"] == tag_id:
            return True
    return False

def get_entity_refs(conn, org_id, schema):
    logger.info("here is the hierarchy")
    cursor = conn.cursor()
    entity_refs = {}
    try:
        sql = """select et.id, et.entity_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum, et.disabled_ts from {}.entity_tag et, {}.tag_def td, {}.org_entity_permission oep  where et.tag_id  = td.id  and oep.entity_id  = et.entity_id and oep.org_id  = {}  and td.name = 'id'""".format(
            schema, schema, schema, org_id,)
        cursor.execute(sql)
        res = cursor.fetchall()
        for r in res:
            entity_refs[str(r[1])] = r[5]

        return entity_refs
    except Exception as e:
        logger.error(e)
        return []
    finally:
        cursor.close()

def get_entities_by_type(entity_types, conn, org_id, tags, entity_refs, schema):
    logger.info("here is the hierarchy")
    cursor = conn.cursor()
    data = []
    columns = ["db_id", "disabled"]
    try:
        for entity_type in entity_types[1]["real_tags"]:
            entity_typ = entity_type.split(" ")
            sql = """select et2.id, entity_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum, et2.disabled_ts, et3.disabled_ts entity_disabled_ts from {}.entity_tag et2, {}.entity et3  where et3.id = et2.entity_id and et2.entity_id in (
                        select entity_id from (
                        select et.entity_id, (','::text || string_agg(td.name::text, ','::text) || ',')  parents from {}.entity_tag et, {}.tag_def td, {}.org_entity_permission oep  where et.tag_id  = td.id  and oep.entity_id  = et.entity_id and oep.org_id  = {} group by et.entity_id) a
                        where ##replace_with_parent_cond##) order by entity_id """.format(schema, schema, schema, schema, schema,
                org_id)
            parent_condition = ""
            for et in entity_typ:
                parent_condition += " parents like '%,{},%' and ".format(et)
            parent_condition = parent_condition[0:-4]
            sql = sql.replace("##replace_with_parent_cond##", parent_condition)
            cursor.execute(sql)
            res = cursor.fetchall()
            entity_id = -1
            entity_data = {}
            i = 0
            for r in res:
                try:
                    if r[1] != entity_id:
                        if entity_data != {}:
                            data.append(entity_data)
                        entity_id = r[1]
                        entity_data = {"db_id" : r[1]}
                    if r[1] == 28038:
                        aaa = 22
                    if i == 0:
                        entity_data["disabled"] = r[12] if r[12] is not None else ""
                    tag_name = tags["tags"][str(r[2])]
                    tag_parent = tags["tag_parents"][str(r[2])]
                    if tag_name not in columns:
                        columns.append(tag_name)
                    if isTagEnum(r[2], tags["enums"]):
                        if r[10] is not None:
                            entity_data[tag_name] =  tags["enums"][str(r[10])]["label"]
                        else:
                            entity_data[tag_name] = r[5]
                        continue
                    if ",str," in tag_parent:
                        entity_data[tag_name] = r[5]
                        continue
                    if ",coord," in tag_parent:
                        entity_data[tag_name] = r[5]
                        continue
                    if ",number," in tag_parent:
                        entity_data[tag_name] = r[3]
                        continue
                    if ",ref," in tag_parent:
                        if tag_name not in entity_data:
                            entity_data[tag_name] = entity_refs[str(r[9])]
                        else:
                            entity_data[tag_name] = entity_data[tag_name] + ",{}".format(entity_refs[str(r[9])])
                        continue
                    if ",marker," in tag_parent:
                        entity_data[tag_name] = '1'
                except Exception as e:
                    raise e
            if entity_data != {}:
                data.append(entity_data)
        return columns, data
    except Exception as e:
        logger.error(e)
        return []
    finally:
        cursor.close()
