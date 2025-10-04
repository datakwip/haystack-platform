from app.model.sqlalchemy import source_object_model, \
    acl_org_model, \
    acl_user_model
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.services import exception_service, \
    tag_def_service, \
    entity_tag_service
from app.services.acl import org_service
from app.model.pydantic.source_objects import entity_schema
from datetime import  datetime
import logging

logger = logging.getLogger(__name__)
def get_entity_by_id(db : Session, entity_id : int, active = True) -> source_object_model.Entity:
    result = db.query(source_object_model.Entity)\
        .filter(source_object_model.Entity.id == entity_id)\
        .filter(source_object_model.Entity.disabled_ts == None)\
        .first() if active else\
        db.query(source_object_model.Entity)\
        .filter(source_object_model.Entity.id == entity_id)\
        .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="entity {} not found".format(entity_id),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )

def get_entity_by_id_tag(db : Session, entity_id_tag : str, active = True) -> source_object_model.Entity:
    result = db.query(source_object_model.Entity)\
        .join(source_object_model.EntityTag, source_object_model.Entity.id == source_object_model.EntityTag.entity_id) \
        .join(source_object_model.TagDef, source_object_model.TagDef.id == source_object_model.EntityTag.tag_id) \
        .filter(source_object_model.TagDef.name == "id")\
        .filter(source_object_model.EntityTag.value_s == entity_id_tag) \
        .filter(source_object_model.Entity.disabled_ts == None)\
        .first() if active else \
        db.query(source_object_model.Entity) \
            .join(source_object_model.EntityTag,
                  source_object_model.Entity.id == source_object_model.EntityTag.entity_id) \
            .join(source_object_model.TagDef, source_object_model.TagDef.id == source_object_model.EntityTag.tag_id) \
            .filter(source_object_model.TagDef.name == "id") \
            .filter(source_object_model.EntityTag.value_s == entity_id_tag) \
            .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="entity with id {} not found".format(entity_id_tag),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )

def get_all(db: Session, user_id, org_id , skip , limit):
    results = []

    result = db.query(source_object_model.Entity)\
        .filter(source_object_model.Entity.id.in_(get_visible_entities_query(db, user_id, org_id)))\
        .offset(skip)\
        .limit(limit)\
        .all()
    for res in result:
        return result
    return results

def get_visible_entities_query(db : Session, user_id : int, org_id : int):

    org_entities_permission_subquery = db.query(acl_org_model.OrgEntityPermission) \
        .filter(acl_org_model.OrgEntityPermission.org_id == org_id) \
        .filter(acl_org_model.OrgEntityPermission.entity_id == source_object_model.Entity.id) \
        .exists()

    user_entity_add_permission_subquery = db.query(acl_user_model.UserEntityAddPermission) \
        .filter(acl_user_model.UserEntityAddPermission.user_id == user_id) \
        .filter(acl_user_model.UserEntityAddPermission.entity_id == source_object_model.Entity.id) \
        .exists()

    user_entity_rev_permission_subquery = ~db.query(acl_user_model.UserEntityRevPermission) \
        .filter(acl_user_model.UserEntityRevPermission.user_id == user_id) \
        .filter(acl_user_model.UserEntityRevPermission.entity_id == source_object_model.Entity.id) \
        .exists()

    subquery = db.query(source_object_model.Entity) \
        .filter(source_object_model.Entity.disabled_ts == None) \
        .filter(or_((org_entities_permission_subquery), (user_entity_add_permission_subquery))) \
        .filter(user_entity_rev_permission_subquery)\
        .with_entities(source_object_model.Entity.id)
    return subquery

def add_entity(db : Session, entity : entity_schema.EntityCreate, user_id):
    db_entity = source_object_model.Entity()
    db.add(db_entity)
    db.flush()
    db.refresh(db_entity)
    for tag in entity.tags:
        db_tag = tag_def_service.get_tag_by_name(tag.tag_name, db)
        entity_tag_service.add_entity_tag(db, tag, db_tag.id, user_id, entity.org_id, db_entity.id  )
    org_service.add_org_entity_permission(db, entity.org_id, db_entity.id)
    return db_entity

def delete_entity(db : Session, entity_id : int):
    db_entity = get_entity_by_id(db, entity_id)
    db_entity.disabled_ts = datetime.now()
    return db_entity



