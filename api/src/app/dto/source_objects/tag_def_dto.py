from sqlalchemy.orm import Session

from app.model.sqlalchemy import source_object_model
from app.model.pydantic.source_objects import tag_def_schema
from app.services import \
    exception_service
from app.services.acl import org_service, user_service
from app.services import tag_def_service,\
    tag_meta_service, \
    tag_enum_service
from typing import Union




def get_tag_def(db: Session, tag_def_id: str, org_id: id, user_id : int):
    tag_id = tag_def_service.get_tag(db, tag_def_id)
    if user_service.is_tag_visible_for_user(db, org_id, user_id, tag_id):
        return tag_def_service.get_tag_by_id(tag_id, db)


def get_tag_defs(db: Session, org_id : int, name:  Union[str, None], user_id : int, skip: int = 0, limit: int = 100):
    return tag_def_service.get_all(db, user_id, org_id, name, skip, limit)

def create_tag_def(db: Session, tag_def: tag_def_schema.TagDefCreate, user_id : int):
    if is_user_admin_for_tag(tag_def, user_id, db):
        try:
            db_tag_def = tag_def_service.add_tag(db, tag_def, user_id)
            tag_id = db_tag_def.id
            tag_meta_service.add_metas(db, tag_def.metas, tag_id, user_id)
            if hasattr(tag_def, 'enums') and tag_def.enums is not None:
                tag_enum_service.add_enums(db, tag_def.enums, tag_id, user_id)
            db.commit()
            return db_tag_def
        except Exception as e:
            db.rollback()
            raise e


def update_tag_def(db: Session, tag_def: tag_def_schema.TagDefUpdate, tag_id : int, user_id : int):
    if user_service.is_user_org_admin(tag_def.org_id, user_id, db)\
            and  user_service.is_tag_visible_for_user(db, tag_def.org_id, user_id, tag_id):
        try:
            db_tag_def = tag_def_service.update_tag(db, tag_def, tag_id, user_id)
            db.commit()
            return db_tag_def
        except Exception as e:
            db.rollback()
            raise e

def is_user_admin_for_tag(tag_def: tag_def_schema.TagDefCreate, user_id : int, db: Session):
    if user_service.is_user_org_admin(tag_def.org_id, user_id, db):
        for meta in tag_def.metas:
            if meta.attribute == "lib":
                return org_service.is_lib_in_org(meta.value, tag_def.org_id, db)
        raise exception_service.BadRequestException(
            exception_service.DtoExceptionObject(
                [exception_service.Detail(
                    msg="lib should be defined in meta",
                    type="value_error.missing",
                    loc=["body", "metas"])],
                exception_service.Ctx(tag_def.json())
            )
        )


def delete_tag_def(db: Session, tag_def : tag_def_schema.TagDefDelete, tag_id : int, user_id : int):
    if user_service.is_user_org_admin(tag_def.org_id, user_id, db)\
            and  user_service.is_tag_visible_for_user(db, tag_def.org_id, user_id, tag_id):
        try:
            db_tag_def = tag_def_service.delete_tag(db, tag_def, tag_id, user_id)
            tag_meta_service.delete_metas_for_tag(db, tag_id)
            tag_enum_service.delete_enums_for_tag(db, tag_id)
            db.commit()
            return db_tag_def
        except Exception as e:
            db.rollback()
            raise e

