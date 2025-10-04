from sqlalchemy.orm import Session
from app.model.pydantic.acl.user import app_user_schema
from app.services.acl import app_user_service, \
    user_service

def create_app_user(db: Session, app_user: app_user_schema.AppUserCreate, user_id : int):
    try:
        if app_user_service.is_user_app_admin(db, user_id):
            db_app_user = app_user_service.add_user(db, app_user)
            db.commit()
            return db_app_user
    except Exception as e:
        db.rollback()
        raise e

def get_app_users(db : Session, user_id : int, skip : int, limit : int):
    if app_user_service.is_user_app_admin(db, user_id):
        return app_user_service.get_all(db, skip, limit)

def get_app_user(db : Session, app_user_id : int, user_id : int):
    if app_user_service.is_user_app_admin(db, user_id):
        return app_user_service.get_app_user_by_id(db, app_user_id)

def delete_app_user(db : Session, app_user_id : int, user_id : int):
    try:
        if app_user_service.is_user_app_admin(db, user_id):
            app_user_service.delete_app_user(db, app_user_id)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e