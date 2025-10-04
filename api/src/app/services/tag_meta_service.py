from app.model.pydantic.source_objects import tag_meta_schema
from app.model.sqlalchemy import source_object_model, history_model, acl_org_model, acl_user_model
from app.services import tag_def_service, tag_hierarchy_service
from sqlalchemy.orm import Session, aliased
from sqlalchemy import or_
from datetime import datetime
from app.services import exception_service

def add_metas(db : Session, metas : list[tag_meta_schema.TagMetaRelationCreate], tag_id : int, user_id : int):
    for meta in metas:
        add_meta(db, meta, tag_id, user_id)


def delete_metas_for_tag(db : Session, tag_id):
    db.query(source_object_model.TagMeta)\
        .filter(source_object_model.TagMeta.tag_id == tag_id)\
        .update({'disabled_ts' : datetime.now()})

def add_meta(db : Session, meta : tag_meta_schema.TagMetaRelationCreate, tag_id : int,  user_id : int):
    attribute = tag_def_service.get_tag_by_name(meta.attribute, db)
    db_tag_meta_result = []
    if meta.value is None:
        meta.value = [None]
    else:
        if type(meta.value) != list:
            meta.value = [meta.value]

    for meta_value in meta.value:
        value = tag_def_service.get_tag_by_name(meta_value, db) if meta.value is not None else None

        db_tag_meta = source_object_model.TagMeta(
            tag_id=tag_id,
            attribute=attribute.id,
            value=value.id if value is not None else None
        )
        db.add(db_tag_meta)
        db.flush()
        db.refresh((db_tag_meta))
        add_meta_history(db, db_tag_meta, user_id)
        tag_def = tag_def_service.get_tag_by_id(attribute.id, db)
        if tag_def.name == "is" and value.id is not None:
            tag_hierarchy_service.add_tag_hierarchy(db, tag_id, value.id, user_id)
        db_tag_meta_result.append(db_tag_meta)
    return db_tag_meta_result

def add_meta_history(db : Session, tag_meta : source_object_model.TagMeta, user_id):
    db_tag_meta_h = history_model.TagMetaHistory(
        id=tag_meta.id,
        tag_id=tag_meta.tag_id,
        attribute=tag_meta.attribute,
        value=tag_meta.value if tag_meta.value is not None else None,
        user_id=user_id,
        modified=datetime.now(),

    )
    db.add(db_tag_meta_h)

def get_meta_by_id(db : Session, meta_id : int, org_id : int, active = True) -> source_object_model.TagMeta:
    result = db.query(source_object_model.TagMeta) \
        .filter(source_object_model.TagMeta.id == meta_id) \
        .filter(source_object_model.TagMeta.disabled_ts == None) \
        .first() if active else \
        db.query(source_object_model.TagMeta) \
            .filter(source_object_model.TagMeta.id == meta_id) \
            .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="meta {} not found".format(meta_id),
                                      type="value.not_found",
                                      loc=["body"])],
            exception_service.Ctx("")
        )
    )
def get_meta_for_tag(db : Session, tag_id : int, org_id : int, active = True) -> list[source_object_model.TagMeta]:
    result = db.query(source_object_model.TagMeta) \
        .filter(source_object_model.TagMeta.tag_id == tag_id) \
        .filter(source_object_model.TagMeta.disabled_ts == None)  if active else \
        db.query(source_object_model.TagMeta) \
            .filter(source_object_model.TagMeta.tag_id == tag_id)
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="meta for tag {} not found".format(tag_id),
                                      type="value.not_found",
                                      loc=["body"])],
            exception_service.Ctx("")
        )
    )
def update_meta(db : Session, meta : tag_meta_schema.TagMetaUpdate, meta_id : int, user_id : int):
    attribute = tag_def_service.get_tag_by_name(meta.attribute, db)
    value = tag_def_service.get_tag_by_name(meta.value, db) if meta.value is not None else None
    db_tag_meta = get_meta_by_id(db, meta_id, meta.org_id)
    if attribute.name == "is" :
        tag_hierarchy_service.update_tag_hierarchy(db, db_tag_meta, meta, user_id)
    db_tag_meta.attribute=attribute.id,
    db_tag_meta.value=value.id if value is not None else None
    add_meta_history(db, db_tag_meta, user_id)
    return db_tag_meta

def delete_meta(db: Session, tag_meta: tag_meta_schema.TagMetaDelete, meta_id : int, user_id : int, org_id : int):
    db_tag_meta = get_meta_by_id(db, meta_id, org_id)
    db_tag_meta.disabled_ts = datetime.now()
    return get_meta_by_id(db, meta_id, False)

def get_all(db: Session, user_id, org_id , skip , limit):
    results = []
    result = db.query(source_object_model.TagMeta)\
        .filter(source_object_model.TagMeta.tag_id.in_(tag_def_service.get_visible_tags_query(db, user_id, org_id)))\
        .offset(skip)\
        .limit(limit)\
        .all()
    for res in result:
        return result
    return results

