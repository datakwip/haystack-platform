from sqlalchemy.orm import Session
from app.model.pydantic.acl.user import user_schema
from app.services.acl import user_service,\
    user_entity_add_permission_service, \
    user_entity_rev_permission_service, \
    user_tag_add_permission_service, \
    user_tag_rev_permission_service, \
    org_service

def create_user(db: Session, user: user_schema.UserCreate, user_id : int):
    try:
        if user_service.is_user_org_admin(user.org_id, user_id, db):
            db_user = user_service.add_user(db, user)
            org_service.add_org_user(db, db_user.id, user.org_id)
            if hasattr(user, 'visible_entities') and user.visible_entities is not None:
                user_entity_add_permission_service.add_user_entity_add_permssions(db, user.visible_entities, db_user.id, user.org_id)
            if hasattr(user, 'invisible_entities') and user.invisible_entities is not None:
                user_entity_rev_permission_service.add_user_entity_rev_permssions(db, user.invisible_entities, db_user.id, user.org_id)
            if hasattr(user, 'visible_tags') and user.visible_tags is not None:
                user_tag_add_permission_service.add_user_tag_add_permssions(db, user.visible_tags, db_user.id, user.org_id)
            if hasattr(user, 'invisible_tags') and user.invisible_tags is not None:
                user_tag_rev_permission_service.add_user_tag_rev_permssions(db, user.invisible_tags, db_user.id, user.org_id)
            db.commit()
            return db_user
    except Exception as e:
        db.rollback()
        raise e

def get_users(db : Session, org_id : int, user_id : int, skip : int, limit : int):
    if user_service.is_user_org_admin(org_id, user_id, db):
        return user_service.get_all(db, org_id, skip, limit)

def get_user(db : Session, user_id : int, org_id :int, current_user_id : int):
    if user_service.is_user_org_admin(org_id, current_user_id, db):
        return user_service.get_user_by_id(db, user_id)

def delete_user(db : Session, user : user_schema.UserDelete, user_id : int, current_user_id : int):
    try:
        if user_service.is_user_org_admin(user.org_id, current_user_id, db):
            db_user = user_service.delete_user(db, user_id)
            db.commit()
            return db_user
    except Exception as e:
        db.rollback()
        raise e