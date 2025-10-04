from sqlalchemy.orm import Session
from app.model.pydantic.source_objects import tag_meta_schema
from app.services import tag_meta_service, tag_def_service
from app.services.acl import user_service
from app.model.sqlalchemy import source_object_model

def forbid_to_delete_meta_for_is_tag(db, db_tag_meta : source_object_model.TagMeta):
    db_tag = tag_def_service.get_tag_by_id(db_tag_meta.attribute, db)
    if db_tag == "is":
        raise Exception("meta for a def with is tag can not be deleted")

def forbid_to_delete_meta_for_default_libraries(db, db_tag_meta : source_object_model.TagMeta, org_id):
    db_lib = tag_def_service.get_tag_by_name("lib", db).id
    db_lib_dk = tag_def_service.get_tag_by_name("lib:dk", db).id
    db_lib_ph = tag_def_service.get_tag_by_name("lib:ph", db).id
    db_lib_phIct = tag_def_service.get_tag_by_name("lib:phIct", db).id
    db_lib_phScience = tag_def_service.get_tag_by_name("lib:phScience", db).id
    db_lib_phIoT = tag_def_service.get_tag_by_name("lib:phIoT", db).id
    libs = [db_lib, db_lib_ph, db_lib_phIct, db_lib_phScience, db_lib_phIoT, db_lib_dk]
    db_tag_metas = tag_meta_service.get_meta_for_tag(db, db_tag_meta.tag_id, org_id)
    for db_tag_meta in db_tag_metas:
        if db_tag_meta.attribute == db_lib and db_tag_meta.value in libs:
            raise Exception("you can not delete metas for default libraries")
def get_tag_metas(db: Session, org_id, user_id : int,  skip: int = 0, limit: int = 100):
    return tag_meta_service.get_all(db, user_id, org_id, skip, limit)

def create_tag_meta(db: Session, tag_meta: list[tag_meta_schema.TagMetaCreate], user_id : int):
    if user_service.is_user_org_admin(tag_meta.org_id, user_id, db)\
            and user_service.is_tag_visible_for_user(db, tag_meta.org_id, user_id, tag_meta.tag_id):
        tag_def_service.get_tag_by_id(tag_meta.tag_id, db)
        db_tag_meta = tag_meta_service.add_meta(db, tag_meta, tag_meta.tag_id, user_id)
        db.commit()
        return db_tag_meta

def update_tag_meta(db: Session, tag_meta: tag_meta_schema.TagMetaUpdate, meta_id : int, user_id : int):
    if user_service.is_user_org_admin(tag_meta.org_id, user_id, db)\
            and user_service.is_meta_visible_for_user(db, tag_meta.org_id, user_id, meta_id):
        db_tag_meta = tag_meta_service.update_meta(db, tag_meta, meta_id, user_id)
        db.commit()
        return db_tag_meta

def delete_tag_meta(db: Session, tag_meta : tag_meta_schema.TagMetaDelete, meta_id : int, user_id : int):
    if user_service.is_user_org_admin(tag_meta.org_id, user_id, db)\
            and user_service.is_meta_visible_for_user(db, tag_meta.org_id, user_id, meta_id):
        try:
            db_tag_meta = tag_meta_service.get_meta_by_id(db, meta_id, tag_meta.org_id)
            forbid_to_delete_meta_for_is_tag(db, db_tag_meta)
            forbid_to_delete_meta_for_default_libraries(db, db_tag_meta, tag_meta.org_id)
            db_tag_def = tag_meta_service.delete_meta(db, tag_meta, meta_id, user_id, tag_meta.org_id)
            db.commit()
            return db_tag_def
        except Exception as e:
            db.rollback()
            raise e


def get_meta_def(db : Session, meta_id : int, org_id : int, user_id : int):
    if user_service.is_meta_visible_for_user(db, org_id, user_id, meta_id):
        return tag_meta_service.get_meta_by_id(db, meta_id, org_id)

