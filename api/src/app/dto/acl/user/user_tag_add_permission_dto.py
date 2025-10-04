from app.model.pydantic.acl.user import user_tag_add_permission_schema
from sqlalchemy.orm import Session
from app.services.acl import user_service, \
    user_tag_add_permission_service


def create_user_tag_add_permission(db : Session, user_tag_add_permission : user_tag_add_permission_schema.UserTagAddPermissionsCreate, user_id : int):
    try:
        if user_service.is_user_org_admin(user_tag_add_permission.org_id, user_id, db):
            db_user_tag_add_permission =  user_tag_add_permission_service.add_user_tag_add_permission(db, user_tag_add_permission, user_id, user_tag_add_permission.org_id)
            db.commit()
            return db_user_tag_add_permission
    except Exception as e:
        db.rollback()
        raise e

def get_user_tag_add_permissions( db : Session,
                                     org_id : int,
                                     user_id : int,
                                     skip : int,
                                     limit : int):
    if user_service.is_user_org_admin(org_id, user_id, db):
        return user_tag_add_permission_service.get_all(db, org_id, skip, limit)

def get_user_tag_add_permission(db, user_object_add_permission_id : int, org_id : int, user_id : int):
        if user_service.is_user_org_admin(org_id, user_id, db):
            return user_tag_add_permission_service.get_user_tag_add_permission_by_id(db, user_object_add_permission_id, org_id)

def delete_user_tag_add_permission(
                db : Session,
                user_tag_add_permission : user_tag_add_permission_schema.UserTagAddPermissionsDelete,
                user_tag_add_permission_id : int,
                user_id : int
            ):
    try:
        if user_service.is_user_org_admin(user_tag_add_permission.org_id, user_id, db):
            user_tag_add_permission_service.delete_user_tag_add_permission(db, user_tag_add_permission, user_tag_add_permission_id)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e