import  db_converter.services.sql_utils_service as sql_utils
import logging

logger = logging.getLogger(__name__)
class EssImporterService:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.sqlUtilsService = sql_utils.ExecuteUtilsService()


    def importData(self):
        #self.importCommunity()
        #self.importPhase()
        #self.importGeoGrid()
        #self.importProperty()
        #self.importSpace()
        #self.importEquipment()
        self.importPoint()


    def importCommunity(self):
        self.cursor.execute("insert into core_dev.\"object\" (value_table_id) select 'community:' || id from \"ESS\".community c ")
        self.cursor.execute("insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) select (select id from core_dev.\"object\" where value_table_id = 'community:'|| c.id) object_id, (select id from core_dev.tag_def td where name = 'dis') tag_id, name from \"ESS\".community c ")
        self.connection.commit()

    def importPhase(self):
        self.sqlUtilsService.addLibrary(self.connection,"ess_lib")
        self.sqlUtilsService.addTag(self.connection, 'communityRef',
                                    [{'attribute' : 'is', 'value' : 'ref'},
                                     {'attribute' : 'lib', 'value' : 'ess_lib'}
                                    ])

        self.cursor.execute("insert into core_dev.\"object\" (value_table_id ) select 'phase:' || id value_table_id from \"ESS\".phase p where id in (46, 49)")
        self.cursor.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) select (select id from core_dev.\"object\" where value_table_id = 'phase:'|| p.id) object_id, (select id from core_dev.tag_def td where name = 'dis') tag_id, name from \"ESS\".phase p where id in (46, 49)"
        )
        self.cursor.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) select (select id from core_dev.\"object\" where value_table_id = 'phase:'|| p.id) object_id, (select id from core_dev.tag_def td where name = 'communityRef') tag_id, (select id from core_dev.\"object\" o where o.value_table_id = 'community:' || p.community_ref) from \"ESS\".phase p where id in (46, 49)"
        )
        self.connection.commit()

    def importGeoGrid(self):
        self.cursor.execute(
            "insert into core_dev.\"object\" (value_table_id )  select 'geogrid:' || id value_table_id from \"ESS\".geo_grid gg ")
        self.cursor.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) select (select id from core_dev.\"object\" where value_table_id = 'geogrid:' || gg.id) object_id, (select id from core_dev.tag_def td where name = 'dis') tag_id, name from \"ESS\".geo_grid gg "
        )
        self.cursor.execute(
           "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) select (select id from core_dev.\"object\" where value_table_id = 'geogrid:' || gg.id) object_id, (select id from core_dev.tag_def td where name = 'communityRef') tag_id, (select id from core_dev.\"object\" o where o.value_table_id = 'community:' || gg.community_ref) from \"ESS\".geo_grid gg"
        )
        self.connection.commit()

    def importProperty(self):
        #self.sqlUtilsService.addTag(self.connection, 'geoGridRef',
        #                            [{'attribute': 'is', 'value': 'ref'},
        #                             {'attribute': 'lib', 'value': 'ess_lib'}
        #                             ])
        #self.sqlUtilsService.addTag(self.connection, 'phaseRef',
        #                            [{'attribute': 'is', 'value': 'ref'},
        #                             {'attribute': 'lib', 'value': 'ess_lib'}
        #                             ])
        #self.cursor.execute(
        #    "insert into core_dev.\"object\" (value_table_id ) select 'property:' || id value_table_id from \"ESS\".property p"
        #)
        #self.cursor.execute(
        #    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) select (select id from core_dev.\"object\" where value_table_id = 'property:' || p.id) object_id, (select id from core_dev.tag_def td where name = 'dis') tag_id, name from \"ESS\".property p"
        #)
        #self.cursor.execute(
        #   "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) select (select id from core_dev.\"object\" where value_table_id = 'property:' || p.id) object_id, (select id from core_dev.tag_def td where name = 'communityRef') tag_id, (select id from core_dev.\"object\" o where o.value_table_id = 'community:' || p.community_ref) from \"ESS\".property p "
        #)
        #self.cursor.execute(
        #    "select (select id from core_dev.\"object\" where value_table_id = 'property:' || p.id) object_id, (select id from core_dev.tag_def td where name = 'geoCoord') tag_id, '{ \"kind\": \"coord\", \"lat\":' || lat || ', \"lng\": ' || long || ' }'  from \"ESS\".property p where id = 106"
        #)
        #self.cursor.execute(
        #    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) select (select id from core_dev.\"object\" where value_table_id = 'property:' || p.id) object_id, (select id from core_dev.tag_def td where name = 'geoGridRef') tag_id, (select id from core_dev.\"object\" o where o.value_table_id = 'geogrid:' || p.geo_grid_ref) from \"ESS\".property p "
        #)
        #self.cursor.execute(
        #    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) select (select id from core_dev.\"object\" where value_table_id = 'property:' || p.id) object_id, (select id from core_dev.tag_def td where name = 'phaseRef') tag_id, (select id from core_dev.\"object\" o where o.value_table_id = 'phase:' || p.phase_ref) from \"ESS\".property p "
        #)
        #self.connection.commit()
        self.importPropertyTags()

    def importPropertyTags(self):
        tags = {}
        self.cursor.execute("select tags from \"ESS\".property where tags is not null")

        records = self.cursor.fetchall()
        self.cursor.close()
        cur = self.connection.cursor()
        for row in records:
            for k in row[0].keys():
                tags[k] = k

        logger.info(tags)

    def importSpace(self):
         self.sqlUtilsService.addTag(self.connection, 'propertyRef',
                                    [{'attribute': 'is', 'value': 'ref'},
                                     {'attribute': 'lib', 'value': 'ess_lib'}
                                     ])
        #self.cursor.execute(
        #    "insert into core_dev.\"object\" (value_table_id ) select 'space:' || id value_table_id from \"ESS\".\"space\" "
        #)
        #self.cursor.execute(
        #    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) select (select id from core_dev.\"object\" where value_table_id = 'space:' || s.id) object_id, (select id from core_dev.tag_def td where name = 'dis') tag_id, name from \"ESS\".space s"
        #)
        # self.cursor.execute(
        #    "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) select (select id from core_dev.\"object\" where value_table_id = 'space:' || s.id) object_id, (select id from core_dev.tag_def td where name = 'propertyRef') tag_id, (select id from core_dev.\"object\" o where o.value_table_id = 'property:' || s.property_ref) from \"ESS\".space s"
        #)

        # self.connection.commit()


    def importEquipment(self):
        #self.cursor.execute(
        #    "insert into core_dev.\"object\" (value_table_id ) select 'equipment:' || id value_table_id from \"ESS\".equipment  "
        #)
        #self.cursor.execute(
        #   "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) select (select id from core_dev.\"object\" where value_table_id = 'equipment:' || e.id) object_id, (select id from core_dev.tag_def td where name = 'dis') tag_id, name from \"ESS\".equipment e"
        #)
        self.cursor.execute(
           "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) select (select id from core_dev.\"object\" where value_table_id = 'equipment:' || e.id) object_id, (select id from core_dev.tag_def td where name = 'spaceRef') tag_id, (select id from core_dev.\"object\" o where o.value_table_id = 'space:' || e.space_ref) from \"ESS\".equipment e"
        )

        #self.connection.commit()

    def importPoint(self):
        self.cursor.execute(
            "insert into core_dev.\"object\" (value_table_id ) select 'esspoint:' || id value_table_id from \"ESS\".point p where p.kind != 'test'"
        )
        self.cursor.execute(
          "insert into core_dev.object_tag_relationship (object_id, tag_id, value_s) select (select id from core_dev.\"object\" where value_table_id = 'esspoint:' || p.id) object_id, (select id from core_dev.tag_def td where name = 'dis') tag_id, name from \"ESS\".point p where p.kind != 'test"
        )
        self.cursor.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_enum) select (select id from core_dev.\"object\" o where o.value_table_id  =  'esspoint:' || p.id) object_id, (select id from core_dev.tag_def td where name = 'kind') tag_id, (select id from core_dev.tag_def_enum where tag_id in (select id from core_dev.tag_def td1 where td1.name = 'kind') and value = (case WHEN p.kind = 'string' THEN 'Str' ELSE p.kind END))  value_n from \"ESS\".point p where p.kind != 'test'"
        )
        self.cursor.execute(
            "insert into core_dev.object_tag_relationship (object_id, tag_id, value_ref) select (select id from core_dev.\"object\" where value_table_id = 'esspoint:' || p.id) object_id, (select id from core_dev.tag_def td where name = 'equipRef') tag_id, (select id from core_dev.\"object\" o where o.value_table_id = 'equipment:' || p.equip_ref) from \"ESS\".point p where p.kind != 'test'"
        )
        # self.connection.commit()


