from app.model.pydantic.acl.org import org_tag_permission_schema
from sqlalchemy.orm import Session
from app.services.acl import org_tag_permission_service, \
    app_user_service, \
    user_service


def create_org_tag_permission(db : Session, org_tag_permission : org_tag_permission_schema.OrgTagPermissionCreate, user_id : int):
    try:
        user_id = user_service.get_current_user(user_id)
        if app_user_service.is_user_app_admin(db, user_id):
            db_org_tag_permission =  org_tag_permission_service.add_org_tag_permission(db, org_tag_permission)
            db.commit()
            return db_org_tag_permission
    except Exception as e:
        db.rollback()
        raise e

def get_org_tag_permissions( db : Session, user_id : int,
                                     skip : int,
                                     limit : int):
    user_id = user_service.get_current_user(user_id)
    if app_user_service.is_user_app_admin(db, user_id):
        return org_tag_permission_service.get_all(db, skip, limit)

def get_org_tag_permission(db, org_tag_permission_id : int, user_id : int):
        user_id = user_service.get_current_user(user_id)
        if app_user_service.is_user_app_admin(db, user_id):
            return org_tag_permission_service.get_org_tag_permission_by_id(db, org_tag_permission_id)

def delete_org_tag_permission(
                db : Session,
                org_object_tag_id : int,
                user_id : int
            ):
    try:
        user_id = user_service.get_current_user(user_id)
        if app_user_service.is_user_app_admin(db, user_id):
            org_tag_permission_service.delete_org_tag_permission(db, org_object_tag_id)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e