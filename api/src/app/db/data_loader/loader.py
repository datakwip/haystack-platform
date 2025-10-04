import csv
import os
import json

from app.db.database import Database
from app.model.sqlalchemy import source_object_model
from app.model.sqlalchemy import aggregate_model
from app.model.sqlalchemy import acl_user_model
from app.model.sqlalchemy import acl_org_model
from app.model.sqlalchemy import history_model
import logging

logger = logging.getLogger(__name__)
class DataLoader():
    def __init__(
            self,
            database_service: Database,
            entity_file_path: str = "../../csv/entity.csv",
            tag_def_file_path: str = "../../csv/tag_def.csv",
            tag_def_h_file_path: str = "../../csv/tag_def_h.csv",
            tag_meta_file_path: str = "../../csv/tag_meta.csv",
            tag_meta_h_file_path: str = "../../csv/tag_meta_h.csv",
            tag_entity_tag_file_path:
            str = "../../csv/entity_tag.csv",
            tag_entity_tag_h_file_path:
            str = "../../csv/entity_tag_h.csv",
            tag_hierarchy_file_path: str = "../../csv/tag_hierarchy.csv",
            tag_hierarchy_h_file_path: str = "../../csv/tag_hierarchy_h.csv",
            tag_def_enum_file_path: str = "../../csv/tag_def_enum.csv",
            tag_def_enum_h_file_path: str = "../../csv/tag_def_enum_h.csv",
            user_file_path: str = "../../csv/user.csv",
            org_file_path: str = "../../csv/org.csv",
            org_admin_file_path: str = "../../csv/org_admin.csv",
            org_user_file_path: str = "../../csv/org_user.csv",
            org_tag_permissions_file_path: str = "../../csv/org_tag_permissions.csv",
            org_entity_permissions_file_path : str = "../../csv/org_entity_permissions.csv"
    ):
        self.__entity_file_path = entity_file_path
        self.__tag_def_file_path = tag_def_file_path
        self.__tag_def_h_file_path = tag_def_h_file_path
        self.__tag_meta_file_path = tag_meta_file_path
        self.__tag_meta_h_file_path = tag_meta_h_file_path
        self.__tag_entity_tag_file_path = tag_entity_tag_file_path
        self.__tag_entity_tag_h_file_path = tag_entity_tag_h_file_path
        self.__tag_hierarchy_file_path = tag_hierarchy_file_path
        self.__tag_hierarchy_h_file_path = tag_hierarchy_h_file_path
        self.__database_service = database_service
        self.__tag_def_enum_file_path = tag_def_enum_file_path
        self.__tag_def_enum_h_file_path = tag_def_enum_h_file_path
        self.__user_file_path = user_file_path
        self.__org_file_path = org_file_path
        self.__org_admin_file_path = org_admin_file_path
        self.__org_user_file_path = org_user_file_path
        self.__org_tag_permissions_file_path = org_tag_permissions_file_path
        self.__org_entity_permissions_file_path = org_entity_permissions_file_path

    def load(self):
        #self.loadUsers()
        #self.loadOrgs()
        #self.loadTagDefs()
        #self.loadTagDefHistory()
        #self.loadTagMetas()
        #self.loadTagMetasHistory()
        #self.loadTagDefEnums()
        #self.loadTagDefEnumsHistory()
        #self.loadEntities()
        #self.loadEntityTag()
        #self.loadEntityTagHistory()
        #self.loadTagHierarchy()
        #self.loadTagHierarchyHistory()
        #self.loadOrgUsers()
        #self.loadOrgAdmins()
        #self.loadOrgTagPermissions()
        self.loadOrgEntityPermissions()

    def loadEntities(self):
        data = self.read_file(self.__entity_file_path)
        s = self.__database_service.get_local_session()
        for entity in data:
            try:
                record = source_object_model.Entity(**{
                    "id": entity["id"],
                    "value_table_id": entity["value_table_id"]
                    if entity["value_table_id"] != ""
                    else None,
                    "disabled_ts": entity["disabled_ts"]
                    if entity["disabled_ts"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def loadTagDefs(self):
        data = self.read_file(self.__tag_def_file_path)
        s = self.__database_service.get_local_session()
        for tag_def in data:
            try:
                record = source_object_model.TagDef(**{
                    "id": tag_def["id"],
                    "name": tag_def["name"],
                    "url": tag_def["url"] if tag_def["url"] != ""
                    else None,
                    "doc": tag_def["doc"] if tag_def["doc"] != ""
                    else None,
                    "dis": tag_def["dis"] if tag_def["dis"] != ""
                    else None,
                    "file_ext": tag_def["file_ext"] if tag_def["file_ext"] != ""
                    else None,
                    "mime": tag_def["mime"] if tag_def["mime"] != ""
                    else None,
                    "version": tag_def["version"] if tag_def["version"] != ""
                    else None,
                    "min_val": tag_def["min_val"]
                    if tag_def["min_val"] != ""
                    else None,
                    "max_val": tag_def["max_val"]
                    if tag_def["max_val"] != ""
                    else None,
                    "base_uri": tag_def["base_uri"] if tag_def["base_uri"] != ""
                    else None,
                    "pref_unit": self.convertStrToList(tag_def["pref_unit"]),
                    "disabled_ts": tag_def["disabled_ts"]
                    if tag_def["disabled_ts"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def loadTagDefHistory(self):
        data = self.read_file(self.__tag_def_h_file_path)
        s = self.__database_service.get_local_session()
        for tag_def_h in data:
            try:
                record = history_model.TagDefHistory(**{
                    "id": tag_def_h["id"],
                    "name": tag_def_h["name"],
                    "url": tag_def_h["url"] if tag_def_h["url"] != ""
                    else None,
                    "doc": tag_def_h["doc"] if tag_def_h["doc"] != ""
                    else None,
                    "dis": tag_def_h["dis"] if tag_def_h["dis"] != ""
                    else None,
                    "file_ext": tag_def_h["file_ext"] if tag_def_h["file_ext"] != ""
                    else None,
                    "mime": tag_def_h["mime"] if tag_def_h["mime"] != ""
                    else None,
                    "version": tag_def_h["version"] if tag_def_h["version"] != ""
                    else None,
                    "min_val": tag_def_h["min_val"]
                    if tag_def_h["min_val"] != ""
                    else None,
                    "max_val": tag_def_h["max_val"]
                    if tag_def_h["max_val"] != ""
                    else None,
                    "base_uri": tag_def_h["base_uri"] if tag_def_h["base_uri"] != ""
                    else None,
                    "pref_unit": self.convertStrToList(tag_def_h["pref_unit"]),
                    "user_id": tag_def_h["user_id"],
                    "modified": tag_def_h["modified"]
                    if tag_def_h["modified"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception as e:
                logger.error(e)
                s.rollback()
            finally:
                s.close()

    def loadTagMetas(self):
        data = self.read_file(self.__tag_meta_file_path)
        s = self.__database_service.get_local_session()
        for tag_meta in data:
            try:
                record = source_object_model.TagMeta(**{
                    "id": tag_meta["id"],
                    "tag_id": tag_meta["tag_id"],
                    "attribute": tag_meta["attribute"],
                    "value": tag_meta["value"]
                    if tag_meta["value"] != ""
                    else None,
                    "disabled_ts": tag_meta["disabled_ts"]
                    if tag_meta["disabled_ts"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def loadTagMetasHistory(self):
        data = self.read_file(self.__tag_meta_h_file_path)
        s = self.__database_service.get_local_session()
        for tag_meta_h in data:
            try:
                record = history_model.TagMetaHistory(**{
                    "id": tag_meta_h["id"],
                    "tag_id": tag_meta_h["tag_id"],
                    "attribute": tag_meta_h["attribute"],
                    "value": tag_meta_h["value"]
                    if tag_meta_h["value"] != ""
                    else None,
                    "user_id": tag_meta_h["user_id"],
                    "modified": tag_meta_h["modified"]
                    if tag_meta_h["modified"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def loadEntityTag(self):
        data = self.read_file(self.__tag_entity_tag_file_path)
        s = self.__database_service.get_local_session()
        for entity_tag in data:
            try:
                record = source_object_model.EntityTag(**{
                    "id": entity_tag["id"],
                    "entity_id": entity_tag["object_id"],
                    "tag_id": entity_tag["tag_id"],
                    "value_n": entity_tag["value_n"]
                    if entity_tag["value_n"] != ""
                    else None,
                    "value_b": entity_tag["value_b"]
                    if entity_tag["value_b"] != ""
                    else None,
                    "value_s": entity_tag["value_s"]
                    if entity_tag["value_s"] != ""
                    else None,
                    "value_ts": entity_tag["value_ts"]
                    if entity_tag["value_ts"] != ""
                    else None,
                    "value_list": entity_tag["value_list"]
                    if entity_tag["value_list"] != ""
                    else [],
                    "value_dict": json.loads(
                        entity_tag["value_dict"]
                    )
                    if entity_tag["value_dict"] != ""
                    else {},
                    "value_ref": entity_tag["value_ref"]
                    if entity_tag["value_ref"] != ""
                    else None,
                    "value_enum": entity_tag["value_enum"]
                    if entity_tag["value_enum"] != ""
                    else None,
                    "disabled_ts": entity_tag["disabled_ts"]
                    if entity_tag["disabled_ts"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def loadEntityTagHistory(self):
        data = self.read_file(self.__tag_entity_tag_h_file_path)
        s = self.__database_service.get_local_session()
        for entity_tag_h in data:
            try:
                record = history_model.EntityTagHistory(**{
                    "id": entity_tag_h["id"],
                    "entity_id": entity_tag_h["object_id"],
                    "tag_id": entity_tag_h["tag_id"],
                    "value_n": entity_tag_h["value_n"]
                    if entity_tag_h["value_n"] != ""
                    else None,
                    "value_b": entity_tag_h["value_b"]
                    if entity_tag_h["value_b"] != ""
                    else None,
                    "value_s": entity_tag_h["value_s"]
                    if entity_tag_h["value_s"] != ""
                    else None,
                    "value_ts": entity_tag_h["value_ts"]
                    if entity_tag_h["value_ts"] != ""
                    else None,
                    "value_list": entity_tag_h["value_list"]
                    if entity_tag_h["value_list"] != ""
                    else [],
                    "value_dict": json.loads(
                        entity_tag_h["value_dict"]
                    )
                    if entity_tag_h["value_dict"] != ""
                    else {},
                    "value_ref": entity_tag_h["value_ref"]
                    if entity_tag_h["value_ref"] != ""
                    else None,
                    "value_enum": entity_tag_h["value_enum"]
                    if entity_tag_h["value_enum"] != ""
                    else None,
                    "user_id": entity_tag_h["user_id"],
                    "modified": entity_tag_h["modified"]
                    if entity_tag_h["modified"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def read_file(self, file_name):
        data = []
        if os.path.exists(file_name):
            with open(file_name) as csvfile:
                data = [
                    {k: v for k, v in row.items()}
                    for row in csv.DictReader(
                        csvfile,
                        delimiter=",",
                        skipinitialspace=True)
                ]
        return data

    def convertStrToList(self, value: str):
        return [] if value == "" else value[2:-2].split(",")


    def loadTagHierarchy(self):
        data = self.read_file(self.__tag_hierarchy_file_path)
        s = self.__database_service.get_local_session()
        for tag_hierarchy in data:
            try:
                record = aggregate_model.TagHierarchy(**{
                    "id": tag_hierarchy["id"],
                    "child_id": tag_hierarchy["child_id"],
                    "parent_id": tag_hierarchy["parent_id"],
                    "disabled_ts": tag_hierarchy["disabled_ts"]
                    if tag_hierarchy["disabled_ts"] != ""
                    else None,

                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def loadTagHierarchyHistory(self):
        data = self.read_file(self.__tag_hierarchy_h_file_path)
        s = self.__database_service.get_local_session()
        for tag_hierarchy_h in data:
            try:
                record = history_model.TagHierarchyHistory(**{
                    "id": tag_hierarchy_h["id"],
                    "child_id": tag_hierarchy_h["child_id"],
                    "parent_id": tag_hierarchy_h["parent_id"],
                    "user_id" : tag_hierarchy_h["user_id"],
                    "modified": tag_hierarchy_h["modified"]
                    if tag_hierarchy_h["modified"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def loadTagDefEnums(self):
        data = self.read_file(self.__tag_def_enum_file_path)
        s = self.__database_service.get_local_session()
        for tag_def_enum in data:
            try:
                record = source_object_model.TagDefEnum(**{
                    "id": tag_def_enum["id"],
                    "tag_id": tag_def_enum["tag_id"],
                    "value": tag_def_enum["value"],
                    "label": tag_def_enum["tag_id"],
                    "disabled_ts": tag_def_enum["disabled_ts"]
                    if tag_def_enum["disabled_ts"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def loadTagDefEnumsHistory(self):
        data = self.read_file(self.__tag_def_enum_h_file_path)
        s = self.__database_service.get_local_session()
        for tag_def_enum_h in data:
            try:
                record = history_model.TagDefEnumHistory(**{
                    "id": tag_def_enum_h["id"],
                    "tag_id": tag_def_enum_h["tag_id"],
                    "value": tag_def_enum_h["value"],
                    "label": tag_def_enum_h["tag_id"],
                    "user_id": tag_def_enum_h["user_id"],
                    "modified": tag_def_enum_h["modified"]
                    if tag_def_enum_h["modified"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                    s.rollback()
            finally:
                s.close()

    def loadUsers(self):
        data = self.read_file(self.__user_file_path)
        s = self.__database_service.get_local_session()
        for user in data:
            try:
                record = acl_user_model.User(**{
                    "id": user["id"],
                    "email": user["email"],
                    "disabled_ts": user["disabled_ts"]
                    if user["disabled_ts"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception:
                s.rollback()
            finally:
                s.close()

    def loadOrgs(self):
        data = self.read_file(self.__org_file_path)
        s = self.__database_service.get_local_session()
        for org in data:
            try:
                record = acl_org_model.Org(**{
                    "id": org["id"],
                    "name": org["name"],
                    "key": org["key"]
                    if org["key"] != ""
                    else None,
                    "disabled_ts": org["disabled_ts"]
                    if org["disabled_ts"] != ""
                    else None,
                })
                s.add(record)
                s.commit()
            except Exception as e:
                logger.error(e)
                s.rollback()
            finally:
                s.close()

    def loadOrgAdmins(self):
        data = self.read_file(self.__org_admin_file_path)
        s = self.__database_service.get_local_session()
        for org in data:
            try:
                record = acl_org_model.OrgAdmin(**{
                    "id": org["id"],
                    "org_id": org["org_id"],
                    "user_id": org["user_id"],
                })
                s.add(record)
                s.commit()
            except Exception as e:
                logger.error(e)
            finally:
                s.close()

    def loadOrgUsers(self):
        data = self.read_file(self.__org_user_file_path)
        s = self.__database_service.get_local_session()
        for org in data:
            try:
                record = acl_org_model.OrgUser(**{
                    "id": org["id"],
                    "org_id": org["org_id"],
                    "user_id": org["user_id"],
                })
                s.add(record)
                s.commit()
            except Exception as e:
                logger.error(e)
                s.rollback()
            finally:
                s.close()

    def loadOrgTagPermissions(self):
        data = self.read_file(self.__org_tag_permissions_file_path)
        s = self.__database_service.get_local_session()
        for org in data:
            try:
                record = acl_org_model.OrgTagPermission(**{
                    "id": org["id"],
                    "org_id": org["org_id"],
                    "tag_id": org["tag_id"],
                })
                s.add(record)
                s.commit()
            except Exception as e:
                logger.error(e)
                s.rollback()
            finally:
                s.close()

    def loadOrgEntityPermissions(self):
        data = self.read_file(self.__org_entity_permissions_file_path)
        s = self.__database_service.get_local_session()
        for org in data:
            try:
                record = acl_org_model.OrgEntityPermission(**{
                    "id": org["id"],
                    "org_id": org["org_id"],
                    "entity_id": org["object_id"],
                })
                s.add(record)
                s.commit()
            except Exception as e:
                logger.error(e)
                s.rollback()
            finally:
                s.close()