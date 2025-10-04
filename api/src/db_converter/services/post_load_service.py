import psycopg2
import  db_converter.services.sql_utils_service as sql_utils
import logging

logger = logging.getLogger(__name__)

class PostLoadService:
    def __init__(self, connection, config):
        self.configService = config
        self.connection = connection
        self.cursor = connection.cursor()
        self.sqlUtilsService = sql_utils.ExecuteUtilsService()
        self.target_connection = psycopg2.connect(dbname=self.configService.getTargetDbName(),
                                user=self.configService.getTargetDbUsername(),
                                password=self.configService.getTargetDbPassword(),
                                host=self.configService.getTargetDbHost(),
                                port=self.configService.getTargetDbPort())

        self.target_cursor = self.target_connection.cursor()

    def load(self):

        #cursor = self.connection.cursor()

        #cursor.execute(
        #    "update   core_dev.object_tag_relationship otr set value_enum = (select id from core_dev.tag_def_enum tde where tde.tag_id = otr.tag_id and (('"' || tde.label|| '"' = value_s or '"' || tde.value || '"' = value_s) or ( tde.label = replace(value_s, 'America/', '') )))   where tag_id in (select id from core_dev.tag_def td where enum != '') and value_n is null")
        #cursor.execute(
        #    "insert into core_dev.object_tag_relationship_h (id, object_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum, user_id, modified) select id, object_id, tag_id, value_n, value_b, value_s, value_ts, value_list, value_dict, value_ref, value_enum, (select id from core_dev.\"user\" u where u.email = 'alexey.matveev@magicbuttonlabs.com'), '01/01/1900 00:00' from core_dev.object_tag_relationship otr "
        #)
        #cursor.execute(
        #    "insert into core_dev.tag_def_h (id, name, url, doc, enum, dis, file_ext, mime, version, min_val, max_val, base_uri, pref_unit, user_id, modified) select  id, name, url, doc, enum, dis, file_ext, mime, version, min_val, max_val, base_uri, pref_unit, (select id from core_dev.\"user\" u where u.email = 'alexey.matveev@magicbuttonlabs.com') user_id , '01/01/1900 00:00' modified from core_dev.tag_def td "
        #)
        #cursor.execute(
        #    "insert into core_dev.tag_meta_h (id, tag_id, attribute, value, user_id, modified) select id, tag_id, attribute, value,  (select id from core_dev.\"user\" u where u.email = 'alexey.matveev@magicbuttonlabs.com') user_id , '01/01/1900 00:00' modified from core_dev.tag_meta tm "
        #)
        #cursor.execute(
        #    "insert into core_dev.tag_def_enum_h (id, tag_id, value, label, user_id, modified) select id, tag_id, value, label, (select id from core_dev.\"user\" u where u.email = 'alexey.matveev@magicbuttonlabs.com') user_id , '01/01/1900 00:00' modified from core_dev.tag_def_enum tde "
        #)

        #cursor.execute(
        #    "insert into core_dev.tag_hierarchy_h (id, child_id, parent_id, user_id, modified) select id, child_id, parent_id,  (select id from core_dev.\"user\" u where u.email = 'alexey.matveev@magicbuttonlabs.com') user_id , '01/01/1900 00:00' modified from core_dev.tag_hierarchy th  "
        #)
        #self.connection.commit()

        self.increaseSequences()


    def increaseSequences(self):
            result = self.target_cursor.execute(
                "SELECT table_name, column_name, column_default from information_schema.columns where column_default  like 'nextval(''core_dev.%'"
            )
            records = self.target_cursor.fetchall()
            self.target_cursor.close()
            for seq in records:
                cur = self.target_connection.cursor()
                cur.execute(
                    "SELECT MAX({}) FROM core_dev.{}".format(seq[1], seq[0])
                )
                curValue = cur.fetchall()[0][0]
                maxValue = curValue + 1 if curValue is not None else 1
                cur.close()
                cur = self.target_connection.cursor()
                cur.execute(
                    "ALTER SEQUENCE {} RESTART {}".format(seq[2].replace("nextval('", "").replace("'::regclass)", ""), str(maxValue))
                )
                self.target_connection.commit()
                cur.close()
                i = 1



