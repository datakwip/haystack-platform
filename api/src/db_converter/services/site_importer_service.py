import  db_converter.services.sql_utils_service as sql_utils
import logging
import json

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.sqlUtilsService = sql_utils.ExecuteUtilsService()


    def importSite(self):
        #self.importSiteIds()
        #self.addTags()
        #self.importSiteTags()
        #self.importYearBuiltTagAttribute()
        self.importMarkers()

    def addTags(self):
        self.sqlUtilsService.addTag('name', 'is', 'str', self.connection)
        self.sqlUtilsService.addTag('address', 'is', 'str', self.connection)



    def importSiteIds(self):
        self.cursor.execute("select * from public.site")

        records = self.cursor.fetchall()
        cur = self.connection.cursor()
        for row in records:
            idStr = str(row[0])
            cur.execute(
                "insert into core_dev.object (value_table_id) values ('site:{}')".format(idStr))
            self.connection.commit()

    def importSiteTags(self):
        self.cursor.execute("select * from public.site")

        records = self.cursor.fetchall()
        self.cursor.close()
        cur = self.connection.cursor()
        for row in records:
            objectId = self.sqlUtilsService.getFirstRow(cur, (), "select value_table_id, id  from core_dev.object where value_table_id = 'site:{}'".format(row[0]))
            #disTag = self.sqlUtilsService.getFirstRow(cur, (),
            #                                          "select name, id  from core_dev.tag_def where name = '{}'".format(
            #                                              'dis'))
            #disTagId = disTag[1]
            #cur.execute(
            #    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) values ({}, '{}', '{}')".format(
            #        objectId[1], disTagId, row[2]))

            #self.importTagsExceptAddress(cur, row, objectId)
            self.importAddressTag(row[4], objectId[1])

            i = 1

    def importTagsExceptAddress(self, cur, row, objectId):
        areaTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                   "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                       'area'))
        areaTagId = areaTag[1]
        cur.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_n) values ({}, '{}', '{}')".format(
                objectId[1], areaTagId, row[3]))
        tzTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                 "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                     'tz'))
        tzTagId = tzTag[1]
        cur.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) values ({}, '{}', '{}')".format(
                objectId[1], tzTagId, row[6]))

        self.connection.commit()

    def importAddressTag(self, addressId, objectId):
        cur = self.connection.cursor()
        row = self.sqlUtilsService.getFirstRow(cur, (), "select * from public.address where id = {}".format(addressId))
        i = 1
        disTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                   "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                       'dis'))
        disTagId = disTag[1]
        cur.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) values ({}, '{}', '{}')".format(
                objectId, disTagId, row[9]))

        geoCity = self.sqlUtilsService.getFirstRow(cur, (),
                                                  "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                      'geoCity'))
        geoCityId = geoCity[1]

        cur.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) values ({}, '{}', '{}')".format(
                objectId, geoCityId, row[3]))

        coord = self.sqlUtilsService.getFirstRow(cur, (),
                                                   "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                       'coord'))
        coordId = coord[1]

        cur.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) values ({}, '{}', '{}')".format(
                objectId, coordId, row[4]))

        geoCoord = { "kind": "coord", "lat": row[5], "lng": row[6] }

        geoCoords = self.sqlUtilsService.getFirstRow(cur, (),
                                                 "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                     'geoCoord'))
        geoCoordId = geoCoords[1]
        cur.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_dict) values ({}, '{}', '{}')".format(
                objectId, geoCoordId, json.dumps(geoCoord)))

        geoPostalCode = self.sqlUtilsService.getFirstRow(cur, (),
                                                     "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                         'geoPostalCode'))
        geoPostalCodeId = geoPostalCode[1]

        cur.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) values ({}, '{}', '{}')".format(
                objectId, geoPostalCodeId, row[7]))

        geoState = self.sqlUtilsService.getFirstRow(cur, (),
                                                         "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                             'geoState'))
        geoStateId = geoState[1]

        cur.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) values ({}, '{}', '{}')".format(
                objectId, geoStateId, json.dumps(row[8])))
        self.connection.commit()


    def importYearBuiltTagAttribute(self):
        self.cursor.execute("select * from public.site where tags != '{}'")

        records = self.cursor.fetchall()
        self.cursor.close()
        cur = self.connection.cursor()
        for row in records:
            tags = row[5]
            if "yearBuilt" in tags:
                objectId = self.sqlUtilsService.getFirstRow(cur, (),
                                                            "select id from core_dev.object where value_table_id = 'site:{}'".format(
                                                                row[0]))
                yearBuiltTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                           "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                               'yearBuilt'))
                yearBuiltTagId = yearBuiltTag[1]

                cur.execute(
                    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_n) values ({}, '{}', '{}')".format(
                        objectId[0], yearBuiltTagId, tags["yearBuilt"]))
                self.connection.commit()
            i = 1


    def importMarkers(self):
        notFoundMarkers = {}
        foundButTags = {}
        self.cursor.execute("select * from public.site where markers != '{}'")

        records = self.cursor.fetchall()
        self.cursor.close()
        cur = self.connection.cursor()
        for row in records:
            objectId = self.sqlUtilsService.getFirstRow(cur, (),
                                                        "select value_table_id, id from core_dev.object where value_table_id = 'site:{}'".format(
                                                            row[0]))

            i = 1
            for marker in row[7]:
                if not self.sqlUtilsService.rowExists("select * from core_dev.tag_def where name = '{}'".format(marker), (), self.connection.cursor()):
                    if marker == "office":
                        cur.execute(
                                    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_n) values ({}, {}, {})".format(
                                        objectId[1], 495, 1131))
                        self.connection.commit()
                    if marker == "apartment":
                        cur.execute(
                                    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_n) values ({}, {}, {})".format(
                                        objectId[1], 495, 1134))
                        self.connection.commit()
                    if marker == "stadium":
                        cur.execute(
                            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_n) values ({}, {}, {})".format(
                                objectId[1], 495, 1164))
                        self.connection.commit()
                    notFoundMarkers[marker] = marker
                    #self.sqlUtilsService.addTag(marker, 'is', 'marker', self.connection)
                else:
                    markerTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                                    "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                                        marker))
                    markerTagId = markerTag[1]
                    isTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                                 "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                                     'is'))
                    isTagId = isTag[1]
                    realMarkerTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                             "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                                 'marker'))
                    realMarkerTagId = realMarkerTag[1]
                    if not self.sqlUtilsService.tagIsOfType(markerTagId, isTagId , realMarkerTagId, self.connection):
                        foundButTags[marker] = marker
                    else:
                        cur.execute(
                            "insert into core_dev.object_tag_relationship (object_id, tag_id) values ({}, '{}')".format(
                                objectId[1], markerTagId))
                        self.connection.commit()


        logger.info(notFoundMarkers)
        logger.info(foundButTags)
