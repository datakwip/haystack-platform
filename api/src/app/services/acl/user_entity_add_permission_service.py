from sqlalchemy.orm import Session
from app.model.pydantic.acl.user import user_entity_add_permission_schema
from app.model.sqlalchemy import acl_user_model, \
    acl_org_model
from app.services.acl import user_service
from app.services import exception_service
def add_user_entity_add_permssions(db : Session, user_entity_add_perms : list[user_entity_add_permission_schema.UserEntityAddPermissionsCreate], user_id : int, org_id : int):
    for permission in user_entity_add_perms:
        add_user_entity_add_permission(db, permission, user_id, org_id)


def add_user_entity_add_permission(db : Session, user_entity_add_perm : user_entity_add_permission_schema.UserEntityAddPermissionsCreate, user_id : int, org_id : int):
    db_user = user_service.get_user_by_email(db, user_entity_add_perm.user_email)
    if user_service.is_entity_visible_for_user(db, org_id=org_id, user_id=db_user.id, entity_id=user_entity_add_perm.entity_id):
        db_user_obj_add_perm = acl_user_model.UserEntityAddPermission(
            user_id = db_user.id,
            entity_id = user_entity_add_perm.entity_id
        )
        db.add(db_user_obj_add_perm)
        db.flush()
        return db_user_obj_add_perm

def get_all(db : Session, org_id : int, skip : int, limit : int):
    results = []

    result = db.query(acl_user_model.UserEntityAddPermission) \
        .join(acl_user_model.User) \
        .join(acl_org_model.OrgUser) \
        .filter(acl_user_model.User.id == acl_user_model.UserTagAddPermission.user_id) \
        .filter(acl_user_model.User.id == acl_org_model.OrgUser.user_id) \
        .filter(acl_org_model.OrgUser.org_id == org_id) \
        .filter(acl_user_model.User.disabled_ts == None) \
        .offset(skip) \
        .limit(limit) \
        .all()
    if result is not None:
        return result
    return results

def get_user_entity_add_permission_by_id(db : Session, user_entity_add_perm_id : int, org_id : int) -> acl_user_model.UserEntityAddPermission:
    result = db.query(acl_user_model.UserEntityAddPermission) \
        .join(acl_user_model.User) \
        .join(acl_org_model.OrgUser) \
        .filter(acl_user_model.UserEntityAddPermission.id == user_entity_add_perm_id) \
        .filter(acl_user_model.User.id == acl_user_model.UserTagAddPermission.user_id) \
        .filter(acl_user_model.User.id == acl_org_model.OrgUser.user_id) \
        .filter(acl_org_model.OrgUser.org_id == org_id) \
        .filter(acl_user_model.User.disabled_ts == None) \
        .first()

    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="entity add permission {} not found".format(user_entity_add_perm_id),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )

def delete_user_entity_add_permission(db : Session, user_entity_add_permission : user_entity_add_permission_schema.UserEntityAddPermissionsDelete, user_entity_add_permission_id : int):
    db_user_entity_add_permission = get_user_entity_add_permission_by_id(db, user_entity_add_permission_id,
                                                                         user_entity_add_permission.org_id)
    if user_service.is_entity_visible_for_user(db, org_id=user_entity_add_permission.org_id, user_id=db_user_entity_add_permission.user_id,
                                               entity_id=db_user_entity_add_permission.entity_id):

        db.delete(db_user_entity_add_permission)