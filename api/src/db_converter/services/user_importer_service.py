import  db_converter.services.sql_utils_service as sql_utils
import logging
import json

logger = logging.getLogger(__name__)

class UserImporterService:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.sqlUtilsService = sql_utils.ExecuteUtilsService()

    def importData(self):
        self.importUsers()

    def importUsers(self):
        self.cursor.execute("insert into core_dev.user (email) values ('alexey.matveev@magicbuttonlabs.com')")
        self.connection.commit()