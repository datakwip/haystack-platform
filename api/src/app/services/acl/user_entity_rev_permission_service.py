from sqlalchemy.orm import Session
from app.model.pydantic.acl.user import user_entity_rev_permission_schema
from app.model.sqlalchemy import acl_user_model,\
    acl_org_model
from app.services.acl import user_service
from app.services import exception_service
def add_user_entity_rev_permssions(db : Session, user_obj_rev_perms : list[user_entity_rev_permission_schema.UserEntityRevPermissionsCreate], user_id : int, org_id : int):
    for permission in user_obj_rev_perms:
        add_user_entity_rev_permission(db, permission, user_id, org_id)


def add_user_entity_rev_permission(db : Session, user_entity_rev_perm : user_entity_rev_permission_schema.UserEntityRevPermissionsCreate, user_id : int, org_id : int):
    if user_service.is_entity_visible_for_user(db, org_id=org_id, user_id=user_id, entity_id=user_entity_rev_perm.entity_id):
        db_user_obj_rev_perm = acl_user_model.UserEntityRevPermission(
            user_id = user_id,
            entity_id = user_entity_rev_perm.entity_id
        )
        db.add(db_user_obj_rev_perm)
        db.flush()
        return db_user_obj_rev_perm

def get_all(db : Session, org_id : int, skip : int, limit : int):
    results = []

    result = db.query(acl_user_model.UserEntityRevPermission) \
        .join(acl_user_model.User) \
        .join(acl_org_model.OrgUser) \
        .filter(acl_user_model.User.id == acl_user_model.UserTagRevPermission.user_id) \
        .filter(acl_user_model.User.id == acl_org_model.OrgUser.user_id) \
        .filter(acl_org_model.OrgUser.org_id == org_id) \
        .filter(acl_user_model.User.disabled_ts == None) \
        .offset(skip) \
        .limit(limit) \
        .all()
    if result is not None:
        return result
    return results

def get_user_entity_rev_permission_by_id(db : Session, user_entity_rev_perm_id : int, org_id : int):
    result = db.query(acl_user_model.UserEntityRevPermission) \
        .join(acl_user_model.User) \
        .join(acl_org_model.OrgUser) \
        .filter(acl_user_model.UserEntityRevPermission.id == user_entity_rev_perm_id) \
        .filter(acl_user_model.User.id == acl_user_model.UserTagRevPermission.user_id) \
        .filter(acl_user_model.User.id == acl_org_model.OrgUser.user_id) \
        .filter(acl_org_model.OrgUser.org_id == org_id) \
        .filter(acl_user_model.User.disabled_ts == None) \
        .first()

    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="entity rev permission {} not found".format(user_entity_rev_perm_id),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )

def delete_user_entity_rev_permission(db : Session, user_entity_rev_permission : user_entity_rev_permission_schema.UserEntityRevPermissionsDelete, user_entity_rev_permission_id : int):
    db_user_entity_rev_permission = get_user_entity_rev_permission_by_id(db, user_entity_rev_permission_id, user_entity_rev_permission.org_id)
    if user_service.is_entity_visible_for_user(db, org_id=user_entity_rev_permission.org_id, user_id=db_user_entity_rev_permission.user_id,
                                               entity_id=db_user_entity_rev_permission.entity_id):
        db.delete(db_user_entity_rev_permission)