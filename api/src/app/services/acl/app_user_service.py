from sqlalchemy.orm import Session
from app.model.sqlalchemy import acl_user_model
from app.model.pydantic.acl.user import app_user_schema
from app.services.acl import user_service
from app.services import exception_service

def get_app_user_by_id(db : Session, app_user_id : int):
    db_app_user = db.query(acl_user_model.AppUser)\
        .join(acl_user_model.User) \
        .filter(acl_user_model.AppUser.id == app_user_id) \
        .filter(acl_user_model.User.disabled_ts == None) \
        .first()
    if db_app_user is not None:
        return db_app_user
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )

def is_user_app_admin(db : Session, user_id : int):
    db_app_user = db.query(acl_user_model.AppUser)\
        .join(acl_user_model.User) \
        .filter(acl_user_model.AppUser.user_id == user_id)\
        .filter(acl_user_model.User.disabled_ts == None) \
        .first()
    if db_app_user is not None:
        return db_app_user
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                      loc=[])],
            exception_service.Ctx("")
        )
    )

def add_user(db : Session, app_user : app_user_schema.AppUserCreate):
    db_user = user_service.get_user_by_email(db, app_user.user_email)
    db_app_user = acl_user_model.AppUser(
        user_id = db_user.id
    )
    db.add(db_app_user)
    db.flush()
    db.refresh(db_app_user)
    return db_app_user

def get_all(db : Session, skip : int, limit : int):
    results = []
    result = db.query(acl_user_model.AppUser) \
        .offset(skip) \
        .limit(limit) \
        .all()
    if result is not None:
        return result
    return results

def delete_app_user(db : Session, app_user_id : int):
    db_app_user = get_app_user_by_id(db, app_user_id)
    db.delete(db_app_user)