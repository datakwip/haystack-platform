import logging
import psycopg2
import db_converter.services.file_service as file_service
import  db_converter.services.site_importer_service as site_importer
import  db_converter.services.equip_importer_service as equip_importer
import  db_converter.services.point_importer_service as point_importer
import  db_converter.services.ess_importer_service as ess_importer
import  db_converter.services.user_importer_service as user_importer
import db_converter.services.post_load_service as post_importer
import  db_converter.services.org_importer_service as org_importer
import  db_converter.services.sql_utils_service as sql_utils
import json

logger = logging.getLogger(__name__)
class ImportJson():
    def __init__(self, config):
        self.configService = config
        self.fileService = file_service.FileService("")
        self.sqlUtilsService = sql_utils.ExecuteUtilsService()


    def importSites(self):
        logger.info("Start importing sites")
        conn = psycopg2.connect(dbname=self.configService.getDbName(),
                                user=self.configService.getDbUsername(),
                                password=self.configService.getDbPassword(),
                                host=self.configService.getDbHost(),
                                port=self.configService.getDbPort())

        #siteImporter = site_importer.ConfigService(conn)
        #siteImporter.importSite()
        #equipImporter = equip_importer.EquipImporterService(conn)
        #equipImporter.importEquip()
        #pointImporter = point_importer.PointImporterService(conn, self.configService)
        #pointImporter.importPoints()
        #essImporter = ess_importer.EssImporterService(conn)
        #essImporter.importData()
        #userImporter = user_importer.UserImporterService(conn)
        #userImporter.importData()
        #orgImporter = org_importer.OrgImporterService(conn)
        #orgImporter.importData()
        postImporter = post_importer.PostLoadService(conn, self.configService)
        postImporter.load()


    def importIntoTable(self):
        logger.info("Start import")
        conn = psycopg2.connect(dbname=self.configService.getDbName(),
                                user=self.configService.getDbUsername(),
                                password=self.configService.getDbPassword(),
                                host=self.configService.getDbHost(),
                                port=self.configService.getDbPort())

        cursor = conn.cursor()
        fileData = self.readFile(self.configService.getFileName())
        fileDataJson = ""
        for line in fileData:
            fileDataJson += line[0:-1]
        fileDataJson = json.loads(fileDataJson)
        #for row in fileDataJson["rows"]:
        #    self.handleEnum(row, cursor, conn)
        #    self.addTag(row,cursor, conn)
        #    self.handleTagFields(row, cursor, conn)
        self.handleTagMetaAndTagHierarchy(cursor, conn, fileDataJson)

    def handleEnum(self, row, cursor, conn):
        if "enum" in row:
            tag = self.sqlUtilsService.getFirstRow(cursor, (),
                                                   "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                       row["def"]["val"]))
            tagId = tag[1]

            enums = row["enum"].split("\n") if row["enum"][0] != "-" else row["enum"][1:].split("\n-")
            for enum in enums:
                values = enum.split(":")
                if len(values) == 2:
                    value = values[0].strip()
                    label = values[1].strip() if values[1].strip() != '' else value
                else:
                    value = values[0]
                    label = value
                cursor.execute(
                    "insert into core_dev.tag_def_enum (tag_id, value, label) values (%s, %s, %s)",
                    (tagId, value, label))
                conn.commit()

    def handleTagMetaAndTagHierarchy(self, cursor, conn, fileDataJson):
        tagHash = {}
        for row in fileDataJson["rows"]:
            tag = self.sqlUtilsService.getFirstRow(cursor, (),
                                                   "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                       row["def"]["val"]))
            tagId = tag[1]
            for rk in row.keys():
                if rk == "children" or rk == "dependsOn" or rk == "def" or rk == "wikipedia" or rk == "doc":
                    continue
                if rk in (
                "enum", "dis", "fileExt", "mime", "version", "minVal", "maxVal", "wikipedia", "doc", "def", "children",
                "baseUri", "prefUnit"):
                    continue
                rkTag = self.sqlUtilsService.getFirstRow(cursor, (),
                                                         "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                             rk))
                rkTagId = rkTag[1]
                if rk not in tagHash:
                    tagHash[rk] = {}
                if not isinstance(row[rk], str) and not isinstance(row[rk], int):
                    if isinstance(row[rk], list):
                        for ll in row[rk]:
                            depTag = self.sqlUtilsService.getFirstRow(cursor, (),
                                                                      "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                                          ll["val"]))
                            depTagId = depTag[1]
                            cursor.execute(
                                "insert into core_dev.tag_meta (tag_id, attribute, value) values (%s, %s, %s)",
                                (tagId, rkTagId, depTagId))
                            conn.commit()
                        tagHash[rk] = row[rk]
                    else:
                        if "val" not in row[rk]:
                            if not self.rowExists(
                                    "select * from core_dev.tag_meta where tag_id = %s and attribute = %s",
                                    (tagId, rkTagId), cursor):
                                cursor.execute(
                                    "insert into core_dev.tag_meta (tag_id, attribute) values (%s, %s)",
                                    (tagId, rkTagId))
                                conn.commit()
                            i = 2
                        else:
                            if not self.rowExists(
                                    "select * from core_dev.tag_meta where tag_id = %s and attribute = %s",
                                    (tagId, rkTagId), cursor):
                                rkValTag = self.sqlUtilsService.getFirstRow(cursor, (),
                                                                            "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                                                row[rk]["val"]))
                                rkValTagId = rkValTag[1]
                                cursor.execute(
                                    "insert into core_dev.tag_meta (tag_id, attribute, value) values (%s, %s, %s)",
                                    (tagId, rkTagId, rkValTagId))
                                conn.commit()
                        for rkk in row[rk].keys():
                            tagHash[rk].update({rkk: row[rk][rkk]})

                else:
                    tagHash[rk] = row[rk]
            if "def" not in row:
                i = 2
            if "val" not in row["def"]:
                i = 3
            if "is" in row:

                for ss in row["is"]:
                    parentTag = self.sqlUtilsService.getFirstRow(cursor, (),
                                                                 "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                                     ss["val"]))
                    parentTagId = parentTag[1]
                    cursor.execute("insert into core_dev.tag_hierarchy (parent_id, child_id) values (%s, %s)",
                                   (parentTagId, tagId))
                    conn.commit()
                    i = 1

                i = 1

    def addTag(self, row, cursor, conn):
        tag = self.sqlUtilsService.getFirstRow(cursor, (),
                                                    "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                        row["def"]["val"]))
        if tag is None:
            cursor.execute("insert into core_dev.tag_def (name, doc, url) values (%s, %s, %s)",
                       (row["def"]["val"], row["doc"], row["wikipedia"]["val"] if "wikipedia" in row else ''))
            conn.commit()

    def handleTagFields(self, row, cursor, conn):
        if "prefUnit" in row:
            cursor.execute("update core_dev.tag_def set pref_unit = %s where name = %s",
                   (row["prefUnit"], row["def"]["val"]))
            conn.commit()
        if "dis" in row:
            cursor.execute("update core_dev.tag_def set dis = %s where name = %s",
                           (row["dis"], row["def"]["val"]))
            conn.commit()
        if "fileExt" in row:
            cursor.execute("update core_dev.tag_def set file_ext = %s where name = %s",
                           (row["fileExt"], row["def"]["val"]))
            conn.commit()
        if "mime" in row:
            cursor.execute("update core_dev.tag_def set mime = %s where name = %s",
                           (row["mime"], row["def"]["val"]))
            conn.commit()
        if "version" in row:
            cursor.execute("update core_dev.tag_def set version = %s where name = %s",
                           (row["version"], row["def"]["val"]))
            conn.commit()
        if "minVal" in row:
            cursor.execute("update core_dev.tag_def set min_val = %s where name = %s",
                           (row["minVal"], row["def"]["val"]))
            conn.commit()
        if "maxVal" in row:
            cursor.execute("update core_dev.tag_def set max_val = %s where name = %s",
                           (row["maxVal"], row["def"]["val"]))
            conn.commit()
        if "wikipedia" in row:
            cursor.execute("update core_dev.tag_def set url = %s where name = %s",
                           (row["wikipedia"]["val"], row["def"]["val"]))
            conn.commit()
        if "doc" in row:
            cursor.execute("update core_dev.tag_def set doc = %s where name = %s",
                           (row["doc"], row["def"]["val"]))
            conn.commit()

        if "baseUri" in row:
            cursor.execute("update core_dev.tag_def set base_uri = %s where name = %s",
                           (row["baseUri"]["val"], row["def"]["val"]))
            conn.commit()

    def readFile(self, fileName):
        return self.fileService.readFileLineByLine(fileName)


    def getData(self, cursor, params, sql):
        cursor.execute(sql, params)
        return cursor.fetchall()

    def rowExists(self, sql, params, cursor):
        rows = self.getData(cursor, params,sql)
        return True if len(rows) > 0 else False

