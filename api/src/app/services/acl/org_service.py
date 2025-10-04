from app.model.sqlalchemy import acl_org_model
from app.model.sqlalchemy import source_object_model, \
    acl_org_model
from sqlalchemy.orm import Session
from app.services import exception_service
from app.model.pydantic.acl.org import org_schema
from datetime import datetime

def is_lib_in_org(lib_name: str, org_id : int, db : Session ):
    result = db.query(acl_org_model.OrgTagPermission)\
        .join(source_object_model.TagDef)\
        .filter(source_object_model.TagDef.name == lib_name)\
        .filter(acl_org_model.OrgTagPermission.org_id == org_id)\
        .limit(1)
    for res in result:
        return True
    raise exception_service.AccessDeniedException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied", loc=[])],
            exception_service.Ctx("")
        )
    )

def add_org_entity_permission(db : Session, org_id : int, entity_id : int):
    db_org_permission = acl_org_model.OrgEntityPermission(
        org_id = org_id,
        entity_id = entity_id
    )
    db.add(db_org_permission)

def add_org_user(db : Session, user_id : int, org_id : int):
    db_org_user = acl_org_model.OrgUser(
        user_id = user_id,
        org_id = org_id
    )
    db.add(db_org_user)
    return db_org_user


def add_org(db : Session,  org : org_schema.OrgCreate):
    db_org = acl_org_model.Org(
        name = org.name,
        key = org.key
    )
    db.add(db_org)
    db.flush()
    db.refresh(db_org)
    return db_org


def get_all(db : Session, skip : int, limit : int):
    result = db.query(acl_org_model.Org) \
    .filter(acl_org_model.Org.disabled_ts == None) \
    .offset(skip) \
    .limit(limit) \
    .all()
    return result if result is not None else []

def get_user_orgs(db : Session, user_id : int, skip : int, limit : int):
    result = db.query(acl_org_model.OrgUser) \
        .filter(acl_org_model.OrgUser.user_id == user_id) \
        .offset(skip) \
        .limit(limit) \
        .all()
    return result if result is not None else []

def is_org_visible_for_user(db : Session, org_id : int, user_id :int):
    result = db.query(acl_org_model.OrgUser) \
        .filter(acl_org_model.OrgUser.user_id == user_id) \
        .filter(acl_org_model.OrgUser.org_id == org_id) \
    .first()
    return True if result is not None else False
def get_org_by_id(db : Session, org_id : int) -> acl_org_model.Org:
    result = db.query(acl_org_model.Org)\
        .filter(acl_org_model.Org.id == org_id)\
        .filter(acl_org_model.Org.disabled_ts == None)\
        .first()

    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="org {} not found".format(org_id),
                                      type="value.not_found",
                                      loc=["body"])],
            exception_service.Ctx("")
        )
    )

def get_org_by_name(db : Session, org_name : str) -> acl_org_model.Org:
    result = db.query(acl_org_model.Org)\
        .filter(acl_org_model.Org.name == org_name)\
        .filter(acl_org_model.Org.disabled_ts == None)\
        .first()

    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="org {} not found".format(org_name),
                                      type="value.not_found",
                                      loc=["body"])],
            exception_service.Ctx("")
        )
    )


def update_org(db : Session, org : org_schema.OrgUpdate, org_id : int):
    db_org = get_org_by_id(db, org_id)
    if org.name is not None:
        db_org.name = org.name
    db_org.key = org.key
    return db_org


def delete_org(db, org_id):
    db_org = get_org_by_id(db, org_id)
    db_org.disabled_ts = datetime.now()
    return db_org