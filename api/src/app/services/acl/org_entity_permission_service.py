
from sqlalchemy.orm import Session
from app.model.pydantic.acl.org import org_entity_permission_schema
from app.model.sqlalchemy import acl_org_model
from app.services.acl import org_service
from app.services import exception_service

def add_org_entity_permission(db : Session, org_entity_perm : org_entity_permission_schema.OrgEntityPermissionCreate):
    db_org = org_service.get_org_by_name(db, org_entity_perm.org_name)
    db_org_entity_perm = acl_org_model.OrgEntityPermission(
            org_id = db_org.id,
            object_id = org_entity_perm.entity_id
        )
    db.add(db_org_entity_perm)
    db.flush()
    return db_org_entity_perm

def get_all(db : Session, skip : int, limit : int):
    result = db.query(acl_org_model.OrgEntityPermission) \
        .offset(skip) \
        .limit(limit) \
        .all()
    return result if  result is not None else []


def get_org_entity_permission_by_id(db : Session, org_object_perm_id : int) -> acl_org_model.OrgEntityPermission:
    result = db.query(acl_org_model.OrgEntityPermission) \
        .filter(acl_org_model.OrgEntityPermission.id == org_object_perm_id) \
        .first()

    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="org object permission {} not found".format(org_object_perm_id),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )

def delete_org_entity_permission(db : Session, org_object_permission_id : int):
    db_org_object_permission = get_org_entity_permission_by_id(db, org_object_permission_id)
    db.delete(db_org_object_permission)