from app.model.pydantic.source_objects import tag_def_enum_schema
from app.services.acl import user_service
from app.services import tag_def_service,\
    tag_enum_service
from sqlalchemy.orm import Session

def create_tag_enum(db: Session, tag_enum: tag_def_enum_schema.TagDefEnumCreate, user_id : int):
    if user_service.is_user_org_admin(tag_enum.org_id, user_id, db):
        db_tag_def = tag_def_service.get_tag_by_name(tag_enum.tag_name, db)
        if user_service.is_tag_visible_for_user(db, tag_enum.org_id, user_id, db_tag_def.id):
            try:
                db_tag_enum = tag_enum_service.add_enum(db, tag_enum, db_tag_def.id, user_id)
                db.commit()
                return db_tag_enum
            except Exception as e:
                db.rollback()
                raise e

def update_tag_enum(db: Session, tag_enum: tag_def_enum_schema.TagDefEnumUpdate, enum_id : int, user_id : int):
    if user_service.is_user_org_admin(tag_enum.org_id, user_id, db):
        try:
            db_tag_enum = tag_enum_service.update_enum(db, tag_enum, enum_id, user_id)
            db.commit()
            return db_tag_enum
        except Exception as e:
            db.rollback()
            raise e

def delete_tag_enum(db: Session, tag_enum : tag_def_enum_schema.TagDefEnumDelete, enum_id : int, user_id : int):
    if user_service.is_user_org_admin(tag_enum.org_id, user_id, db):
        try:
            db_tag_enum = tag_enum_service.delete_enum(db, tag_enum, enum_id, user_id, tag_enum.org_id)
            db.commit()
            return db_tag_enum
        except Exception as e:
            db.rollback()
            raise e

def get_enum_for_tag(db: Session, org_id, user_id : int, tag_id, skip: int = 0, limit: int = 100):
    return tag_enum_service.get_enum_for_tag(db, user_id, org_id, tag_id, skip, limit)

def get_tag_enums(db: Session, org_id, user_id : int,  skip: int = 0, limit: int = 100):
    return tag_enum_service.get_all(db, user_id, org_id,  skip, limit)

def get_tag_def_enum(db : Session, enum_id : int, org_id : int, user_id : int):
    db_tag_enum = tag_enum_service.get_enum_by_id(db, enum_id)
    if user_service.is_tag_visible_for_user(db, org_id=org_id, user_id=user_id, tag_id=db_tag_enum.tag_id):
        return db_tag_enum

def get_tag_enum_by_value(db : Session, tag_id : int, value : str):
    return tag_enum_service.get_tag_enum_by_value(db, tag_id, value)