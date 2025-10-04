from app.model.pydantic.source_objects import entity_tag_schema
from app.model.sqlalchemy import source_object_model, history_model
from sqlalchemy.orm import Session
from app.services import entity_service, \
    exception_service
from app.services.acl import user_service
from datetime import datetime
from app.services import tag_def_service

def isEntityVirtualPoint(db: Session, entity_id : int, active = True):
    tag_id = tag_def_service.get_tag_by_name('virtualPoint', db).id
    result = db.query(source_object_model.EntityTag) \
        .filter(source_object_model.EntityTag.entity_id == entity_id) \
        .filter(source_object_model.EntityTag.disabled_ts == None) \
        .filter(source_object_model.EntityTag.tag_id == tag_id) \
        .first() if active else \
        db.query(source_object_model.EntityTag) \
            .filter(source_object_model.EntityTag.entity_id == entity_id) \
            .filter(source_object_model.EntityTag.disabled_ts == None) \
            .first()
    if result is not None:
        return True
    else:
        return False

def get_entity_tag_by_id(db : Session, entity_tag_id : int, active = True) -> source_object_model.EntityTag:
    result = db.query(source_object_model.EntityTag)\
        .filter(source_object_model.EntityTag.id == entity_tag_id)\
        .filter(source_object_model.EntityTag.disabled_ts == None)\
        .first() if active else\
        db.query(source_object_model.EntityTag)\
        .filter(source_object_model.EntityTag.id == entity_tag_id)\
        .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="entity {} not found".format(entity_tag_id),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )


def add_entity_tag(db : Session, obj_rel : entity_tag_schema.EntityTagCreate, tag_id : int, user_id : int, org_id : int, entity_id : int):
    if user_service.is_tag_visible_for_user(db, org_id, user_id, tag_id):
        db_entity_tag = source_object_model.EntityTag(
        entity_id=entity_id,
        tag_id = tag_id,
        value_n = obj_rel.value_n if obj_rel.value_n is not None else None,
        value_b =  obj_rel.value_b if obj_rel.value_b is not None else None,
        value_s =  obj_rel.value_s if obj_rel.value_s is not None else None,
        value_ts =  obj_rel.value_ts if obj_rel.value_ts is not None else None,
        value_list =  obj_rel.value_list if obj_rel.value_list is not None else [],
        value_dict =  obj_rel.value_dict if obj_rel.value_dict is not None else None,
        value_ref =  obj_rel.value_ref if obj_rel.value_ref is not None else None,
        value_enum =  obj_rel.value_enum if obj_rel.value_enum is not None else None,
        )
        db.add(db_entity_tag)
        db.flush()
        db.refresh(db_entity_tag)
        add_entity_tag_history(db, obj_rel, tag_id, user_id, entity_id, db_entity_tag.id)
        return db_entity_tag

def add_entity_tag_history(db : Session, obj_rel : entity_tag_schema.EntityTagBase, tag_id : int, user_id : int, entity_id : int, obj_rel_id : int):
        db_entity_tag_h = history_model.EntityTagHistory(
            id = obj_rel_id,
            entity_id=entity_id,
            tag_id=tag_id,
            value_n=obj_rel.value_n if obj_rel.value_n is not None else None,
            value_b=obj_rel.value_b if obj_rel.value_b is not None else None,
            value_s=obj_rel.value_s if obj_rel.value_s is not None else None,
            value_ts=obj_rel.value_ts if obj_rel.value_ts is not None else None,
            value_list=obj_rel.value_list if obj_rel.value_list is not None else [],
            value_dict=obj_rel.value_dict if obj_rel.value_dict is not None else {},
            value_ref=obj_rel.value_ref if obj_rel.value_ref is not None else None,
            value_enum=obj_rel.value_enum if obj_rel.value_enum is not None else None,
            user_id = user_id,
            modified=datetime.now()
        )
        db.add(db_entity_tag_h)


def get_all(db: Session, user_id, org_id , tag_id : int, value_s : str, skip , limit):
    results = []
    if tag_id is None:
        result = db.query(source_object_model.EntityTag)\
            .filter(source_object_model.EntityTag.entity_id.in_(entity_service.get_visible_entities_query(db, user_id, org_id)))\
            .offset(skip)\
            .limit(limit)\
            .all()
    else:
        search = "%{}%".format(value_s if value_s is not None else '')
        result = db.query(source_object_model.EntityTag) \
            .filter(
            source_object_model.EntityTag.entity_id.in_(entity_service.get_visible_entities_query(db, user_id, org_id))) \
            .filter(source_object_model.EntityTag.tag_id == tag_id) \
            .filter(source_object_model.EntityTag.value_s.like(search)) \
            .offset(skip) \
            .limit(limit) \
            .all()
    for res in result:
        return result
    return results

def update_entity_tag(db: Session, entity_tag : entity_tag_schema.EntityTagUpdate, entity_tag_id : int, user_id : int):
    db_entity_tag = get_entity_tag_by_id(db, entity_tag_id)
    if user_service.is_entity_visible_for_user(db, org_id=entity_tag.org_id, user_id=user_id,
                                               entity_id=db_entity_tag.entity_id):
        if entity_tag.value_n is not None:
            db_entity_tag.value_n = entity_tag.value_n
        if entity_tag.value_b is not None:
            db_entity_tag.value_b = entity_tag.value_b
        if entity_tag.value_s is not None:
            db_entity_tag.value_s = entity_tag.value_s
        if entity_tag.value_ts is not None:
            db_entity_tag.value_ts = entity_tag.value_ts
        if entity_tag.value_list is not None:
            db_entity_tag.value_list = entity_tag.value_list
        if entity_tag.value_dict is not None:
            db_entity_tag.value_dict = entity_tag.value_dict
        if entity_tag.value_ref is not None:
            db_entity_tag.value_ref = entity_tag.value_ref
        if entity_tag.value_enum is not None:
            db_entity_tag.value_enum = entity_tag.value_enum

        add_entity_tag_history(db, entity_tag, db_entity_tag.tag_id, user_id, db_entity_tag.entity_id, db_entity_tag.id)
        return db_entity_tag

def delete_entity_tag(db : Session, entity_tag : entity_tag_schema.EntityTagDelete, objtagrel_id : int, user_id : int):
    db_entity_tag = get_entity_tag_by_id(db, objtagrel_id)
    if user_service.is_entity_visible_for_user(db, org_id=entity_tag.org_id, user_id=user_id,
                                               entity_id=db_entity_tag.object_id):
        db_entity_tag.disabled_ts = datetime.now()
        return db_entity_tag

