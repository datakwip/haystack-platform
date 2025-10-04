import logging

logger = logging.getLogger(__name__)

def get_all_refs(conn, org_id,schema):
    logger.info("here is the hierarchy")
    cursor = conn.cursor()
    try:
        refs = []
        sql = "select td.id, td.name from {}.entity_tag et, {}.tag_def td, {}.org_entity_permission oep where et.entity_id = oep.entity_id and oep.org_id = {} and et.tag_id  = td.id and td.name like '%Ref' group by td.name, td.id".format(
            schema, schema, schema,org_id)
        cursor.execute(sql)
        res = cursor.fetchall()
        for r in res:
            refs.append({"id": r[0], "name": r[1]})
        return refs
    except Exception as e:
        logger.error(e)
        return []
    finally:
        cursor.close()

def get_entity_types(conn, org_id, tag_hierarchy, schema):
    logger.info("here is the hierarchy")
    cursor = conn.cursor()
    hierarchy = {}
    try:
        sql = "select tags from (select (','::text || string_agg(td.name::text, ','::text)) || ','::text AS tags from {}.entity_tag et, {}.tag_def td, {}.org_entity_permission oep where et.entity_id = oep.entity_id and oep.org_id = {} and et.tag_id  = td.id group by et.entity_id) a group by tags".format(
            schema, schema, schema, org_id)
        cursor.execute(sql)
        res = cursor.fetchall()
        for r in res:
            tags = r[0].split(",")
            temp_tags = []
            real_tags = []
            for tag in tags:
                if tag in tag_hierarchy:
                    if tag_hierarchy[tag] not in temp_tags:
                        temp_tags.append(tag_hierarchy[tag] )
                    if tag not in real_tags:
                        real_tags.append(tag )
            tagsAsString = ""
            realTagsAsString=""
            if len(temp_tags) > 0:
                real_tags.sort()
                temp_tags.sort()
                tagsAsString = " ".join(temp_tags)
                realTagsAsString = " ".join(real_tags)
            if tagsAsString != "":
                if tagsAsString not in hierarchy:
                    hierarchy[tagsAsString] = {"len" : len(temp_tags), "real_tags" : [realTagsAsString]}
                else:
                    if realTagsAsString not in hierarchy[tagsAsString]["real_tags"]:
                        hierarchy[tagsAsString]["real_tags"].append(realTagsAsString)
        return  sorted(hierarchy.items(), key=lambda x:x[1]["len"], reverse=True)
    except Exception as e:
        logger.error(e)
        return []
    finally:
        cursor.close()

def getEntityDirectChildren(conn, schema):
    cursor = conn.cursor()
    direct_children = []
    try:
        sql = "select td2.name from {}.tag_hierarchy th, {}.tag_def td, {}.tag_def td2  where th.parent_id = td.id and td.name = 'entity' and td2.id = th.child_id ".format(
            schema, schema, schema)
        cursor.execute(sql)
        res = cursor.fetchall()
        for r in res:
            direct_children.append(r[0])
        return direct_children
    except Exception as e:
        logger.error(e)
        return []
    finally:
        cursor.close()

def convert_refs_to_entity_markers(refs):
    entity_markers = []
    for ref in refs:
        entity_markers.append("'{}'".format(ref["name"].replace("Ref", "")))
    return entity_markers

def get_entity_children(entity, ref_hierarchy, parents):
    logger.info(entity)
    dict = {}
    if "{}Ref".format(entity) not in ref_hierarchy:
        return {}
    for ref in ref_hierarchy["{}Ref".format(entity)]:
        if entity == ref["name"]:
            dict[ref["name"]] = {entity : {}}
            continue
        if ref["name"] in parents.split(","):
            dict[ref["name"]] = {entity : {}}
            continue
        parents+=",{}".format(entity)
        print(parents)
        dict[ref["name"]] = get_entity_children(ref["name"], ref_hierarchy, parents)
    return dict
def get_hierarchy_tree(conn, org_id, refs, entity_markers, schema):
    logger.info("here is the hierarchy")
    ref_hierarchy = {}
    entity_hierarchy = {}
    for ref in refs:
        cursor = conn.cursor()
        try:
            ref_hierarchy[ref["name"]] = []
            sql = "select  td2.id, td2.name from {}.entity_tag et2, {}.tag_def td2 where et2.tag_id = td2.id and et2.entity_id  in (select et.entity_id from {}.entity_tag et, {}.tag_def td, {}.org_entity_permission oep where et.entity_id = oep.entity_id and oep.org_id = {} and et.tag_id  = td.id and et.tag_id = {} ) and td2.name in ({}) group by td2.id, td2.name".format(
                schema, schema, schema, schema, schema, org_id, ref["id"], ",".join(entity_markers))
            cursor.execute(sql)
            res = cursor.fetchall()
            for r in res:
                ref_hierarchy[ref["name"]].append({"id": r[0], "name": r[1]})
                if r[1] not in entity_hierarchy:
                    entity_hierarchy[r[1]]  = []
                entity_hierarchy[r[1]].append(ref["name"])
        except Exception as e:
            logger.error(e)
        finally:
            cursor.close()
    hierarchy = {}
    for entity_marker in entity_markers:
        entity = entity_marker.replace("'", "")
        if entity not in entity_hierarchy.keys():
            hierarchy[entity] = get_entity_children("{}".format(entity), ref_hierarchy, "")
    return hierarchy
def get_tag_hierarchy(conn, org_id, schema):
    entity_children = getEntityDirectChildren(conn, schema)
    cursor = conn.cursor()
    tag_hierarchy = {}
    try:
        sql = "select  td.id, td.name, tdp.parent_ids from {}.tag_def_parents tdp, {}.tag_def td, {}.tag_meta tm, {}.tag_def td2 where tm.\"attribute\"  = td2.id and td2.name = 'mandatory' and tm.tag_id = td.id and   tdp.tag_id = td.id and tdp.parent_ids like '%,entity,%' group by td.id, td.name, tdp.parent_ids".format(schema, schema, schema, schema)
        cursor.execute(sql)
        res = cursor.fetchall()
        for r in res:
            for entity_child in entity_children:
                tag_hierarchy[entity_child] = entity_child
                parents = r[2].split(",")
                if "{}".format(entity_child) in parents:
                    if r[1] in tag_hierarchy:
                        print(" {} has multiple entities. old {} new {}".format(r[1], tag_hierarchy[r[1]], entity_child))
                    tag_hierarchy[r[1]] = entity_child
        return tag_hierarchy

    finally:
        cursor.close()
def get_entity_hierarchy(conn, org_id, tag_hierarchy, schema):
    logger.info("here is the hierarchy")
    entity_types = get_entity_types(conn, org_id, tag_hierarchy, schema)
    return entity_types


