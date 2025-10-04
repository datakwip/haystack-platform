
def get_tags(conn, schema):
    cursor = conn.cursor()
    tags = {}
    try:
        sql = "select td.id, td.name, tdp.parent_ids from {}.tag_def_parents tdp, {}.tag_def td where tdp.tag_id = td.id".format(schema, schema)
        cursor.execute(sql)
        res = cursor.fetchall()
        for r in res:
            tags[r[0]] = {"db_id": r[0], "name" : r[1], "parents": r[2]}
        return tags

    finally:
        cursor.close()