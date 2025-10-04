import  db_converter.services.sql_utils_service as sql_utils
import logging
import concurrent.futures
import traceback

logger = logging.getLogger(__name__)

class PointImporterService:
    def __init__(self, connection, config):
        self.connection = connection
        self.cursor = connection.cursor()
        self.sqlUtilsService = sql_utils.ExecuteUtilsService()
        self.configService = config
        self.notFoundMarkers = {}

    def importPoints(self):
        #self.importPointEnitities()
        #self.importPointColumns()
        self.importMarkers()
        #self.importTags()

    def importTags(self):
            notFoundTags = {}
            self.cursor.execute("select * from public.point where tags != '{}'")

            records = self.cursor.fetchall()
            self.cursor.close()
            cur = self.connection.cursor()
            for row in records:
                for marker in row[4]:
                    realMarker = marker
                    if not self.sqlUtilsService.rowExists(
                            "select * from core_dev.tag_def where name = '{}'".format(realMarker), (),
                            self.connection.cursor()):
                        if realMarker in notFoundTags:
                            notFoundTags[realMarker] = notFoundTags[realMarker] + 1
                        else:
                            notFoundTags[realMarker] = 1
            logger.info(notFoundTags)

    def importMarkers(self):
        self.cursor.execute("select * from public.point where markers != '{}'")

        records = self.cursor.fetchall()
        self.cursor.close()
        cur = self.connection.cursor()
        isTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                 "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                     'is'))
        self.isTagId = isTag[1]
        realMarkerTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                         "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                             'marker'))
        self.realMarkerTagId = realMarkerTag[1]
        rows = []
        for row in records:
            rows.append(row)
            if len(rows) >20:
                with concurrent.futures.ThreadPoolExecutor(
                        max_workers=self.configService.getThreads(), thread_name_prefix="point_markers_importer"
                ) as executor:
                    executor.map(self.importPointMarkers, rows)
                rows = []
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.configService.getThreads(), thread_name_prefix="point_markers_importer"
        ) as executor:
            executor.map(self.importPointMarkers, rows)


        logger.info(self.notFoundMarkers)

    def importPointMarkers(self, row):
        try:
            cur = self.connection.cursor()
            for marker in row[7]:
                realMarker = marker
                markerTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                             "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                                 realMarker))
                if markerTag is None:
                    if realMarker in self.notFoundMarkers:
                        self.notFoundMarkers[realMarker] = self.notFoundMarkers[realMarker] + 1
                    else:
                        self.notFoundMarkers[realMarker] = 0
                    continue
                markerTagId = markerTag[1]

                if not markerTag or not self.sqlUtilsService.tagIsOfType(markerTagId, self.isTagId, self.realMarkerTagId,
                                                                         self.connection):
                    if realMarker in self.notFoundMarkers:
                        self.notFoundMarkers[realMarker] = self.notFoundMarkers[realMarker] + 1
                    else:
                        self.notFoundMarkers[realMarker] = 0
                else:
                    objectId = self.sqlUtilsService.getFirstRow(cur, (),
                                                                "select value_table_id, id from core_dev.object where value_table_id = 'point:{}'".format(
                                                                    row[0]))
                    if not self.sqlUtilsService.rowExists(
                            "select * from core_dev.object_tag_relationship where object_Id = '{}' and tag_id = {}".format(
                                objectId[1], markerTagId), (), self.connection.cursor()):
                        cur.execute(
                            "insert into core_dev.object_tag_relationship (object_id, tag_id) values ({}, '{}')".format(
                                objectId[1], markerTagId))
                        self.connection.commit()
        except Exception as e:
            logger.error("Error on line {} {}".format(e.__traceback__.tb_lineno, traceback.format_exc()))

    def importPointEnitities(self):
        self.cursor.execute("select * from public.point ")

        records = self.cursor.fetchall()
        cur = self.connection.cursor()
        for row in records:
            idStr = str(row[0])
            cur.execute(
                "insert into core_dev.object (value_table_id) values ('point:{}')".format(idStr))
            self.connection.commit()

    def importPointColumns(self):
        self.cursor.execute("select * from public.point")

        records = self.cursor.fetchall()
        cur = self.connection.cursor()
        equipRefTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                 "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                     'equipRef'))
        equipRefTagId = equipRefTag[1]

        kindTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                       "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                           'kind'))
        kindTagId = kindTag[1]
        # equipRef = 244
        #cur.execute(
        #    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) select (select id from core_dev.\"object\" o where o.value_table_id = 'point:' || p.id) object_id, '{}', (select id from core_dev.\"object\" o where o.value_table_id  = 'equip:' || p.equip_ref) value_ref from public.point p".format(equipRefTagId))
        #self.connection.commit()
        #cur.execute("insert into core_dev.object_tag_relationship (object_id, tag_id, value_enum) select (select id from core_dev.\"object\" o where o.value_table_id  =  'point:' || p.id) object_id, {}, (select id from core_dev.tag_def_enum where tag_id = {} and value = (case WHEN p.kind = 'string' THEN 'Str' ELSE p.kind END))  value_n from public.point p where kind is not null ".format(kindTagId, kindTagId))
        #self.connection.commit()
        cur.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) select (select id from core_dev.\"object\" o where o.value_table_id  =  'point:' || p.id) object_id, (select id from core_dev.tag_def where name = 'dis'), dis value_s from public.point p ")
        self.connection.commit()



        #for row in records:

            #equipId = self.sqlUtilsService.getFirstRow(cur, (),
            #                                          "select * from core_dev.object where point_table_id = '{}'".format(
            #                                              row[3]))
            #cur.execute(
            #    "insert into core_dev.object_tag_relationship (object_id, tagdef_id, value_ref) values ({}, '{}', '{}')".format(
            #        objectId[1], 'equipRef', equipId[1]))


            # cur.execute(
            #    "insert into core_dev.object_tag_relationship (object_id, tagdef_id, value_s) values ({}, '{}', '{}')".format(
            #       objectId[1], 'location', row[5]))


            #self.connection.commit()