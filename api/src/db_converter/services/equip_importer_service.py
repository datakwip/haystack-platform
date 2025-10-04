import  db_converter.services.sql_utils_service as sql_utils
import logging
import json

logger = logging.getLogger(__name__)
class EquipImporterService:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.sqlUtilsService = sql_utils.ExecuteUtilsService()

    def importEquip(self):
        #self.importEquipObjects()
        #self.addTags()
        #self.addEquipFields()
        self.importMarkers()

    def addTags(self):
        self.sqlUtilsService.addTag("location", "is", "str", self.connection)

    def importEquipObjects(self):
        self.cursor.execute("select * from public.equip")

        records = self.cursor.fetchall()
        cur = self.connection.cursor()
        for row in records:
            idStr = str(row[0])
            cur.execute(
                "insert into core_dev.object (value_table_id) values ('equip:{}')".format(idStr))
            self.connection.commit()

    def addEquipFields(self):
        self.cursor.execute("select * from public.equip")

        records = self.cursor.fetchall()
        cur = self.connection.cursor()
        for row in records:
            objectId = self.sqlUtilsService.getFirstRow(cur, (),
                                                        "select value_table_id, id from core_dev.object where value_table_id = 'equip:{}'".format(
                                                            row[0]))
            disTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                         "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                             'dis'))
            disTagId = disTag[1]


            cur.execute(
                "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) values ({}, '{}', '{}')".format(
                    objectId[1], disTagId, row[2]))

            #cur.execute(
            #    "insert into core_dev.object_tag_relationship (object_id, tagdef_id, value_s) values ({}, '{}', '{}')".format(
            #       objectId[1], 'location', row[5]))

            siteRefTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                      "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                          'siteRef'))
            siteRefTagId = siteRefTag[1]

            siteId = self.sqlUtilsService.getFirstRow(cur, (),
                                                        "select value_table_id, id from core_dev.object where value_table_id = 'site:{}'".format(
                                                            row[3]))
            cur.execute(
                "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) values ({}, '{}', '{}')".format(
                   objectId[1], siteRefTagId, siteId[1]))
            self.connection.commit()



    def importMarkers(self):
        notExistingTags = {}
        self.cursor.execute("select * from public.equip where markers != '{}'")

        records = self.cursor.fetchall()
        self.cursor.close()
        cur = self.connection.cursor()
        isTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                 "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                     'is'))
        isTagId = isTag[1]
        realMarkerTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                         "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                             'marker'))
        realMarkerTagId = realMarkerTag[1]
        for row in records:
            objectId = self.sqlUtilsService.getFirstRow(cur, (),
                                                        "select value_table_id, id from core_dev.object where value_table_id = 'equip:{}'".format(
                                                            row[0]))

            for marker in row[6]:
                realMarkerObject = self.getMarkerValue(marker)
                realMarker = realMarkerObject[0]
                realMarkerValue = realMarkerObject[0] if len(realMarkerObject) > 1 else None

                markerTag = self.sqlUtilsService.getFirstRow(cur, (),
                                                             "select name, id  from core_dev.tag_def where name = '{}'".format(
                                                                 realMarker))
                if markerTag is None:
                    notExistingTags[realMarker] = realMarker
                    continue
                markerTagId = markerTag[1]

                if realMarkerValue is not None:
                    realMarkerValue = 1124


                if markerTagId:

                    if realMarker not in ("perimeter","interior", 'mutuallink', 'mach', 'baseboard', 'ibss', 'testahu', 'primary', 'secondary', 'freezer', 'refrigerator', 'newTestMarker', 'updatedMarker', 'test', 'compressor') :
                        i = 1
                        #self.sqlUtilsService.addTag(marker, 'is', 'marker', self.connection)

                    if not self.sqlUtilsService.tagIsOfType(markerTagId, isTagId, realMarkerTagId, self.connection):
                        notExistingTags[realMarker] = realMarker

                    if markerTagId is not None and not self.sqlUtilsService.rowExists("select * from core_dev.object_tag_relationship where object_id = {} and tag_id = '{}'".format(objectId[1], markerTagId), (), self.connection.cursor()):
                        if realMarkerValue is None:
                            cur.execute(
                                "insert into core_dev.object_tag_relationship (object_id, tag_id) values ({}, '{}')".format(
                                objectId[1], markerTagId))
                            self.connection.commit()
                        else:
                            cur.execute(
                                "insert into core_dev.object_tag_relationship (object_id, tag_id, value_n) values ({}, '{}', '{}')".format(
                                objectId[1], markerTagId, realMarkerValue))
                            self.connection.commit()
                    #self.connection.commit()
                #else:
                #    if realMarker not in ("perimeter", "interior", "mutuallink", 'mach',  'baseboard', 'ibss'):
                #        i = 1

        logger.info(notExistingTags)

    def getMarkerValue(self, marker):
        markers = {'manufacturing' : ['primaryFunction', 'Manufacturing/Industrial Plant'],
                   'constantVolume' : ['constantAirVolume'],
                   'dxCool' : ['dxCooling'],
                   'elecHeat' : ['elecHeating'],
                   'openLoop' : ['condenserOpenLoop'],
                   'closedLoop' : ['condenserClosedLoop'],
                   'rooftop' : ['rtu'],
                   'chilledWaterPlant' : ['chilled'],
                   'condenserWaterPlant' : ['condenserLoop'],
                   'hotWaterHeat' : ['hotWaterHeating'],
                   }

        if marker in markers.keys():
            return markers[marker]
        else:
            return [marker]
