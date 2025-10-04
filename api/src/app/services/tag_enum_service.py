from app.model.pydantic.source_objects import tag_def_enum_schema
from sqlalchemy.orm import Session
from datetime import datetime
from app.model.sqlalchemy import history_model
from app.services import tag_def_service\
    , exception_service
from app.services.acl import user_service
from app.model.sqlalchemy import source_object_model

def get_enum_by_id(db : Session, enum_id : int, active = True) -> source_object_model.TagDefEnum:
    result = db.query(source_object_model.TagDefEnum)\
        .filter(source_object_model.TagDefEnum.id == enum_id)\
        .filter(source_object_model.TagDefEnum.disabled_ts == None)\
        .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="enum {} not found".format(enum_id),
                                      type="value.not_found",
                                      loc=["body"])],
            exception_service.Ctx("")
        )
    )

def add_enums(db : Session, enums : list[tag_def_enum_schema.TagDefEnumRelationCreate], tag_id, user_id):
    for enum in enums:
        add_enum(db, enum, tag_id, user_id)


def delete_enums_for_tag(db : Session, tag_id):
    db.query(source_object_model.TagDefEnum)\
        .filter(source_object_model.TagDefEnum.tag_id == tag_id)\
        .update({'disabled_ts' : datetime.now()})

def add_enum(db : Session, enum : tag_def_enum_schema.TagDefEnumRelationCreate, tag_id : int, user_id : int):
    db_tag_def_enum = source_object_model.TagDefEnum(
            tag_id=tag_id,
            value=enum.value,
            label=enum.label,
        )
    db.add(db_tag_def_enum)
    db.flush()
    db.refresh(db_tag_def_enum)
    add_enum_history(db, enum, tag_id, user_id, db_tag_def_enum.id)
    return db_tag_def_enum

def add_enum_history(db : Session, enum : tag_def_enum_schema.TagDefEnumRelationCreate, tag_id, user_id, enum_id):
    db_tag_def_enum_h = history_model.TagDefEnumHistory(
        id=enum_id,
        tag_id=tag_id,
        value=enum.value,
        label=enum.label,
        user_id=user_id,
        modified=datetime.now(),
    )
    db.add(db_tag_def_enum_h)

def update_enum(db : Session, tag_enum : tag_def_enum_schema.TagDefEnumUpdate, enum_id : int, user_id : int):
    db_enum = get_enum_by_id(db, enum_id)
    db_tag_def = tag_def_service.get_tag_by_id(db_enum.tag_id, db)
    if user_service.is_tag_visible_for_user(db, tag_enum.org_id, user_id, db_tag_def.id):
        db_enum = get_enum_by_id(db, enum_id)
        db_enum.value = tag_enum.value
        db_enum.label = tag_enum.label
        add_enum_history(db, tag_enum, db_enum.tag_id, user_id, enum_id)
        return db_enum

def delete_enum(db: Session, tag_enum: tag_def_enum_schema.TagDefEnumDelete, enum_id : int, user_id : int, org_id : int):
    db_tag_enum = get_enum_by_id(db, enum_id)
    db_tag_enum.disabled_ts = datetime.now()
    return db_tag_enum

def get_all(db: Session, user_id, org_id , skip , limit):
    results = []
    result = db.query(source_object_model.TagDefEnum)\
        .filter(source_object_model.TagDefEnum.tag_id.in_(tag_def_service.get_visible_tags_query(db, user_id, org_id)))\
        .offset(skip)\
        .limit(limit)\
        .all()
    for res in result:
        return result
    return results

def get_enum_for_tag(db: Session, user_id, org_id , tag_id, skip , limit):
    results = []
    result = db.query(source_object_model.TagDefEnum)\
        .filter(source_object_model.TagDefEnum.tag_id.in_(tag_def_service.get_visible_tags_query(db, user_id, org_id))) \
        .filter(source_object_model.TagDefEnum.tag_id == tag_id) \
        .offset(skip)\
        .limit(limit)\
        .all()
    for res in result:
        return result
    return results


def get_tag_enum_by_value(db : Session, tag_id : int, value : str, active = True):
    result = db.query(source_object_model.TagDefEnum) \
        .filter(source_object_model.TagDefEnum.tag_id == tag_id) \
        .filter(source_object_model.TagDefEnum.disabled_ts == None) \
        .filter(source_object_model.TagDefEnum.value == value) \
        .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="enum for tag {} with value {} not found".format(tag_id, value),
                                      type="value.not_found",
                                      loc=["body"])],
            exception_service.Ctx("")
        )
    )