from sqlalchemy.orm import Session
from app.services import entity_tag_service, \
    tag_def_service
from app.services.acl import user_service
from app.model.pydantic.source_objects import entity_tag_schema

def get_entity_tags(db: Session, org_id : int, tag_id : str, value_s : str, user_id : int, skip: int = 0, limit: int = 100):
    tag_id = tag_def_service.get_tag(db, tag_id) if tag_id is not None else None
    return entity_tag_service.get_all(db, user_id, org_id, tag_id, value_s, skip, limit)



def create_entity_tag(
        db: Session,
        entity_tag: entity_tag_schema.EntityTagCreateWithEntityId,
        user_id : int
    ):
    try:
        if user_service.is_user_org_admin(db=db, user_id = user_id, org_id = entity_tag.org_id) \
                and user_service.is_entity_visible_for_user(db, org_id=entity_tag.org_id, user_id=user_id, entity_id=entity_tag.entity_id):
            db_tag = tag_def_service.get_tag_by_name(entity_tag.tag_name, db)
            db_entity_tag_relationship = entity_tag_service.add_entity_tag(db, entity_tag, db_tag.id, user_id, entity_tag.org_id, entity_tag.entity_id)
            db.commit()
            return db_entity_tag_relationship
    except Exception as e:
        db.rollback()
        raise e

def get_entity_tag(db: Session, entitytag_id: int, org_id : int, user_id : int):
    db_entity_tag = entity_tag_service.get_entity_tag_by_id(db,  entitytag_id)
    if user_service.is_entity_visible_for_user(db, org_id=org_id, user_id=user_id, entity_id=db_entity_tag.entity_id):
        return db_entity_tag

def update_entity_tag(db : Session, entity_tag : entity_tag_schema.EntityTagUpdate, entitytag_id : int, user_id : int):
    try:
        if user_service.is_user_org_admin(db=db, user_id=user_id, org_id=entity_tag.org_id):
            db_entity_tag =  entity_tag_service.update_entity_tag(db, entity_tag, entitytag_id, user_id)
            db.commit()
            return db_entity_tag
    except Exception as e:
        db.rollback()
        raise e


def delete_entity_tag(db: Session, entity_tag : entity_tag_schema.EntityTagDelete, entitytag_id : int, user_id : int):
    try:
        if user_service.is_user_org_admin(db=db, user_id=user_id, org_id=entity_tag.org_id):
            db_objtagrel =  entity_tag_service.delete_entity_tag(db ,entity_tag, entitytag_id, user_id)
            db.commit()
            return db_objtagrel
    except Exception as e:
        db.rollback()
        raise e


