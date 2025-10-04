import  db_converter.services.sql_utils_service as sql_utils
import logging
import json

logger = logging.getLogger(__name__)

class OrgImporterService:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.sqlUtilsService = sql_utils.ExecuteUtilsService()

    def importData(self):
        #self.importOrgs()
        #self.importOrgUsers()
        #self.importOrgAdmins()
        self.importOrgTagPermissions()
        self.importOrgObjectPermissions()

    def importOrgs(self):
        self.cursor.execute("insert into core_dev.org (name) values ('public')")
        self.cursor.execute("insert into core_dev.org (name) values ('ess')")
        self.connection.commit()

    def importOrgUsers(self):
        self.cursor.execute("insert into core_dev.org_user (user_id, org_id) select (select id from core_dev.user where email = 'alexey.matveev@magicbuttonlabs.com') user_id, id from core_dev.org")
        self.connection.commit()

    def importOrgAdmins(self):
        self.cursor.execute("insert into core_dev.org_admin (user_id, org_id) select (select id from core_dev.user where email = 'alexey.matveev@magicbuttonlabs.com') user_id, id from core_dev.org")
        self.connection.commit()

    def importOrgTagPermissions(self):
        self.cursor.execute("insert into core_dev.org_tag_permission (org_id, tag_id)  select (select id from core_dev.org where name = 'public') org_id , id from core_dev.tag_def td where name in ('lib:ph', 'lib:phIct', 'lib:phIoT', 'lib:phScience')")
        self.cursor.execute(
            "insert into core_dev.org_tag_permission (org_id, tag_id)  select (select id from core_dev.org where name = 'ess') org_id , id from core_dev.tag_def td where name in ('lib:ph', 'lib:phIct', 'lib:phIoT', 'lib:phScience', 'ess_lib')")
        self.connection.commit()

    def importOrgObjectPermissions(self):
        self.cursor.execute("insert into core_dev.org_object_permission (org_id, object_id) select (select id from core_dev.org where name = 'public') org_id , id from core_dev.\"object\" o where o.value_table_id like 'site:%' or o.value_table_id like 'equip:%' or o.value_table_id like 'point:%'")
        self.cursor.execute("insert into core_dev.org_object_permission (org_id, object_id) select (select id from core_dev.org where name = 'ess') org_id , id from core_dev.\"object\" o where not (o.value_table_id like 'site:%' or o.value_table_id like 'equip:%' or o.value_table_id like 'point:%')")
        self.connection.commit()
