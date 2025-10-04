from sqlalchemy.orm import Session
from app.model.pydantic.acl.org import org_schema
from app.services.acl import org_service,\
    app_user_service, \
    user_service

def create_org(db: Session, org: org_schema.OrgCreate, user_id : int):
    try:
        if app_user_service.is_user_app_admin(db, user_id):
            db_user = org_service.add_org(db, org)
            db.commit()
            return db_user
    except Exception as e:
        db.rollback()
        raise e

def get_orgs(db : Session,  user_id : int, skip : int, limit : int):
    if app_user_service.is_user_app_admin(db, user_id):
        return org_service.get_all(db, skip, limit)

def get_current_user_orgs(db : Session, user_id : int, skip : int, limit : int):
    return org_service.get_user_orgs(db, user_id, skip, limit)

def get_org(db : Session, org_id :int, user_id : int):
    if app_user_service.is_user_app_admin(db, user_id):
        return org_service.get_org_by_id(db, org_id)

def update_org(db : Session,  org : org_schema.OrgUpdate,  org_id : int, user_id : int):
    try:
        if app_user_service.is_user_app_admin(db, user_id):
            db_org = org_service.update_org(db, org, org_id)
            db.commit()
            return db_org
    except Exception as e:
        db.rollback()
        raise e

def delete_org(db : Session, org_id : int, user_id : int):
    try:
        if app_user_service.is_user_app_admin(db, user_id):
            db_org = org_service.delete_org(db, org_id)
            db.commit()
            return db_org
    except Exception as e:
        db.rollback()
        raise e