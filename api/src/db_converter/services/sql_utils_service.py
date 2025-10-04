import logging

logger = logging.getLogger(__name__)
class ExecuteUtilsService:
    def getData(self, cursor, params, sql):
        cursor.execute(sql, params)
        return cursor.fetchall()

    def rowExists(self, sql, params, cursor):
        rows = self.getData(cursor, params,sql)
        return True if len(rows) > 0 else False

    def getFirstRow(self, cursor, params, sql):
        rows = self.getData(cursor, params, sql)
        if len(rows) != 0:
            return rows[0]
        return None

    def addTag(self, tagId, attribute, value, connection):
        cur = connection.cursor()
        if not self.rowExists("select * from core_dev.tag_def where id = '{}'".format(tagId), (), cur):
            cur.execute(
                "insert into core_dev.tag_def (id) values ('{}')".format(tagId))
            cur.execute(
                "insert into core_dev.tag_meta (tag_id, attribute, value) values ('{}', '{}', '{}')".format(tagId, attribute, value))
            connection.commit()
            logger.info("tag {} added {} {}".format(tagId, attribute, value))

    def tagIsOfType(self, tagId, attribute, value, connection):
        cur = connection.cursor()
        exists = self.rowExists(
            "select * from core_dev.tag_meta where tag_id = '{}' and attribute= '{}' and value = '{}'".format(tagId,
                                                                                                              attribute,
                                                                                                              value),
                (), cur)
        if exists:
            return True
        parent = tagId
        while True:
            parent = self.getFirstRow(cur, (), "select value from core_dev.tag_meta where tag_id = '{}' and attribute= '{}'".format(parent, attribute))
            if parent is None:
                return False
            parent = parent[0]
            exists = self.rowExists("select * from core_dev.tag_meta where tag_id = '{}' and attribute= '{}' and value = '{}'".format(parent, attribute, value), (), cur)
            if exists:
                return True
        return False

    def addLibrary(self, connection,libraryName):
        cur = connection.cursor()
        cur.execute("insert into core_dev.tag_def  (name) values ('{}')".format(libraryName))
        cur.execute(
            "insert into core_dev.tag_meta (tag_id, attribute, value) select id tag_def, (select id from core_dev.tag_def td where name = 'is') attr, (select id from core_dev.tag_def td2 where name = 'lib') val from core_dev.tag_def td where name = '{}'".format(libraryName))
        cur.execute(
            "insert into core_dev.tag_hierarchy (child_id, parent_id) select id child_id, (select id from core_dev.tag_def td2 where name = 'lib') parent_id from core_dev.tag_def td where name = '{}'".format(libraryName))
        connection.commit()

    def addTag(self, connection, tagName, attributes):
        cur = connection.cursor()
        cur.execute("insert into core_dev.tag_def  (name) values ('{}')".format(tagName))
        for attr in attributes:
            cur.execute(
                "insert into core_dev.tag_meta (tag_id, attribute, value) select id tag_def, (select id from core_dev.tag_def td where name = '{}') attr, (select id from core_dev.tag_def td2 where name = '{}') val from core_dev.tag_def td where name = '{}'".format(
                    attr["attribute"], attr["value"], tagName))
            if attr["attribute"] == "is":
                cur.execute(
                    "insert into core_dev.tag_hierarchy (child_id, parent_id) select id child_id, (select id from core_dev.tag_def td2 where name = '{}') parent_id from core_dev.tag_def td where name = '{}'".format(
                        attr["value"], tagName))

        connection.commit()
