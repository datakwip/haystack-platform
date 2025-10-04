import json
import datetime
import os
from app.services.export.services import entity_service
def getTagsBySql(conn, schema):
    resTags = {}
    resTagIs = {}
    cursor = conn.cursor()
    try:
        sql = "select id, name from {}.tag_def".format(schema)
        cursor.execute(sql)
        tags = cursor.fetchall()
        for r in tags:
            tag_id = r[0]
            tag_name = r[1]
            if str(tag_id) in resTags:
                print ("key {} for tag {} {} already in tags".format(tag_id, tag_id, tag_name))
            resTags[str(tag_id)] = tag_name
            if tag_name in resTags:
                print ("key {} for tag {} {} already in tags".format(tag_name,tag_id, tag_name))
            resTags[tag_name] =tag_id

        sql = "select tag_id, parent_ids from {}.tag_def_parents".format(schema)
        cursor.execute(sql)
        tags = cursor.fetchall()
        for r in tags:
            tag_id = r[0]
            tag_parent_ids = r[1]
            if str(tag_id) in resTagIs:
                print("key {} for tag {} {} already in tags".format(tag_id, tag_id, tag_parent_ids))
            resTagIs[str(tag_id)] = tag_parent_ids

        resEnums = {}
        sql = "select id, tag_id, value, label from {}.tag_def_enum".format(schema)
        cursor.execute(sql)
        tags = cursor.fetchall()
        for r in tags:
            id = r[0]
            tag_id= r[1]
            value=r[2]
            label=r[3]
            if str(id) in resEnums:
                print("key {} for enum already in tags".format(id))
            resEnums[str(id)] = {"id" : id, "tag_id" : tag_id, "value": value, "label": label}
        return {"tags": resTags, "tag_parents": resTagIs, "enums": resEnums}
    finally:
        cursor.close()



def getEntityBySql(entity_id, conn, org_id, schema):
    cursor = conn.cursor()
    try:
        error = False
        entity_db_id = -1
        result = []
        sql = "select id, entity_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum from {}.entity_tag where entity_id in (select et.entity_id from {}.entity_tag et, {}.tag_def td, {}.org_entity_permission oep  where et.tag_id = td.id and td.name = 'id' and et.value_s = '{}' and oep.entity_id = et.entity_id and org_id = {}) ".format(schema, schema, schema, schema,
            entity_id, org_id)

        if isinstance(entity_id, int):
            sql = "select et.id, et.entity_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum from {}.entity_tag et, {}.org_entity_permission oep where et.entity_id = {} and oep.entity_id = et.entity_id and oep.org_id = {}".format(schema, schema,
                entity_id, org_id)

        cursor.execute(sql)
        tags = cursor.fetchall()
        for r in tags:
            if entity_db_id == -1:
                entity_db_id = r[1]
            else:
                if entity_db_id != r[1]:
                    error = True
                    break
            tag = {
                "id" : r[0],
                "entity_id" : entity_db_id,
                "tag_id" : r[2],
                "value_n" : r[3],
                "value_b" : r[4],
                "value_s" : r[5],
                "value_ts" : r[6],
                "value_list" : r[7],
                "value_dict" : r[8],
                "value_ref" : r[9],
                "value_enum" : r[10],
            }
            result.append(tag)
        if error:
            print("more than one entity found for {}".format(entity_id))
        if len(tags) > 0:
            return {"id" : entity_db_id, "tags" : result}
        else:
            print("entity {} not found".format(entity_id))
        return None
    finally:
       cursor.close()
def getEntitiesBySql(take_from_db, entities, folders, entity_type, allEntities, conn, org_id, schema, file_name = None, by_db_id = False):
    if take_from_db:
        result_entities = {}
        j = 1
        for entity in entities: 
            #print("enriching {} {} out {}".format(entity["id"], j, len(entities)))
            j += 1
            db_entity = None
            if entity.get("db_id") is None and entity.get("id") is None:
                continue
            if by_db_id and entity.get("db_id") is not None and entity.get("db_id") != "":
                val = int(entity["db_id"])
                db_entity = getEntityBySql(val, conn, org_id, schema)
            else:
                val = entity_service.get_value(entity["id"])
                db_entity = getEntityBySql(val, conn, org_id, schema)

            if db_entity is not None:
                entity_string_id = entity_service.get_id_value_from_tags(db_entity["tags"])
                result_entities[entity["id"]] =  { "db_entity" : db_entity, "file_entity" : entity}
            else:
                result_entities[entity["id"]] = { "file_entity": entity}
        outputDict = {"type" : entity_type , "entities" : result_entities}
        os.makedirs(folders, exist_ok=True)
        with open("{}{}.json".format(folders, entity_type if file_name is None else file_name), "w") as outfile:
            outfile.write(json.dumps(outputDict,default=str))
        if entity_type in allEntities and "entities" in allEntities[entity_type] and len(allEntities[entity_type]["entities"].keys()) > 0:
            outputDict["entities"].update(allEntities[entity_type]["entities"])
        allEntities[entity_type] = outputDict
        return outputDict
    else:
        outputDict =  json.load(open("{}{}.json".format(folders, entity_type if file_name is None else file_name)))
        if entity_type in allEntities and "entities" in allEntities[entity_type] and len(allEntities[entity_type]["entities"].keys()) > 0:
            outputDict["entities"].update(allEntities[entity_type]["entities"])
        allEntities[entity_type] = outputDict
        return outputDict

def addNewValueBySql(valueToUpdate, entity_id, tag_id, tags, conn, schema):
    cursor = conn.cursor()
    try:
        row_id = getAvailabeEntityTagBySql(entity_id, tag_id, conn, schema)
        if row_id is not None:
            if not entity_service.isTagMarker(tag_id, tags):
                updateExistingValueBySql(valueToUpdate, row_id, conn, schema)
        else:
            sql = "insert into {}.entity_tag( entity_id, tag_id, {}) values ({}, {}, {})".format(schema, valueToUpdate[0],
                                                                                                   entity_id, tag_id,
                                                                                                   getValueForSql(
                                                                                                       valueToUpdate))
            if valueToUpdate[0] == 'marker_true' and valueToUpdate[1] == 'marker_true':
                sql = "insert into {}.entity_tag( entity_id, tag_id) values ({}, {})".format(schema, entity_id, tag_id)
            res = cursor.execute(sql)
            row_id = getAvailabeEntityTagBySql(entity_id, tag_id, conn, schema)
            sql = "select id, entity_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum, {}, '{}' from {}.entity_tag where id = {}".format(2, datetime.datetime.now().isoformat(), schema, row_id)
            sql = "insert into {}.entity_tag_h(id, entity_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum, user_id, modified) {} ".format(schema, sql)
            res = cursor.execute(sql)
            conn.commit()
    finally:
        cursor.close()

def getAvailabeEntityTagBySql(entity_id, tag_id, conn, schema):
    cursor = conn.cursor()
    try:
        row_id = None
        sql = "select id from {}.entity_tag where entity_id = {} and tag_id = {}".format(schema, entity_id, tag_id)
        cursor.execute(sql)
        tags = cursor.fetchall()
        for r in tags:
            row_id = r[0]
            return row_id
    finally:
        cursor.close()

def getValueForSql(valueToUpdate):
    return "'{}'".format(valueToUpdate[1]) if valueToUpdate[0] == "value_s" else "{}".format(valueToUpdate[1])


def updateExistingValueBySql(valueToUpdate, row_id, conn, schema):
    cursor = conn.cursor()
    try:
        sql = "update {}.entity_tag set {} = {} where id = {}".format(schema, valueToUpdate[0], getValueForSql(valueToUpdate), row_id)
        res = cursor.execute(sql)
        sql = "select id, entity_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum, user_id, '{}' from {}.entity_tag_h where id = {}".format(datetime.datetime.now().isoformat(), schema, row_id)
        sql= sql.replace(valueToUpdate[0], "{}".format(getValueForSql(valueToUpdate)))
        sql = "insert into {}.entity_tag_h(id, entity_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum, user_id, modified) {} ON CONFLICT DO NOTHING ".format(schema, sql)
        res = cursor.execute(sql)
        conn.commit()
    finally:
        cursor.close()
