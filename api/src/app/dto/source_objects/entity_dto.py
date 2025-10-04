from sqlalchemy.orm import Session

from app.model.pydantic.source_objects import entity_schema
from app.services import entity_service
from app.services.acl import user_service


def get_entity(db: Session, entity_id: str, org_id : int, user_id : int):
    try:
        entity_id_local = int(entity_id)
    except Exception:
        entity_id_local = entity_service.get_entity_by_id_tag(db, entity_id).id
    if user_service.is_entity_visible_for_user(db, org_id= org_id, user_id = user_id, entity_id = entity_id_local):
        return entity_service.get_entity_by_id(db,  entity_id_local)


def get_entities(db: Session, org_id : int, user_id : int,  skip: int = 0, limit: int = 100):
    return entity_service.get_all(db, user_id, org_id, skip, limit)


def create_entity(db: Session, entity: entity_schema.EntityCreate, user_id : int):
    try:
        if user_service.is_user_org_admin(entity.org_id, user_id, db):
            db_entity = entity_service.add_entity(db, entity, user_id)
            db.commit()
            return db_entity
    except Exception as e:
        db.rollback()
        raise e

def delete_entity(db: Session, entity: entity_schema.EntityDelete, entity_id : int, user_id : int):
    try:
        if user_service.is_user_org_admin(entity.org_id, user_id, db):
            db_entity = entity_service.delete_entity(db,  entity_id)
            db.commit()
            return db_entity
    except Exception as e:
        db.rollback()
        raise e

