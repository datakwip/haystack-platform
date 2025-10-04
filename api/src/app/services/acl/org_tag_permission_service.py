from sqlalchemy.orm import Session
from app.model.pydantic.acl.org import org_tag_permission_schema
from app.model.sqlalchemy import acl_org_model
from app.services.acl import org_service
from app.services import exception_service, \
    tag_def_service

def add_org_tag_permission(db : Session, org_tag_perm : org_tag_permission_schema.OrgTagPermissionCreate):
    db_org = org_service.get_org_by_name(db, org_tag_perm.org_name)
    db_tag = tag_def_service.get_tag_by_name(org_tag_perm.tag_name, db)
    db_org_tag_perm = acl_org_model.OrgTagPermission(
            org_id = db_org.id,
            tag_id = db_tag.id
        )
    db.add(db_org_tag_perm)
    db.flush()
    return db_org_tag_perm

def get_all(db : Session, skip : int, limit : int):
    result = db.query(acl_org_model.OrgTagPermission) \
        .offset(skip) \
        .limit(limit) \
        .all()
    return result if  result is not None else []


def get_org_tag_permission_by_id(db : Session, org_tag_perm_id : int) -> acl_org_model.OrgEntityPermission:
    result = db.query(acl_org_model.OrgTagPermission) \
        .filter(acl_org_model.OrgTagPermission.id == org_tag_perm_id) \
        .first()

    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="org tag permission {} not found".format(org_tag_perm_id),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )

def delete_org_tag_permission(db : Session, org_tag_permission_id : int):
    db_org_tag_permission = get_org_tag_permission_by_id(db, org_tag_permission_id)
    db.delete(db_org_tag_permission)