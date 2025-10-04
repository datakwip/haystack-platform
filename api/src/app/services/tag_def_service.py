from sqlalchemy.orm import Session, aliased
from datetime import datetime
from app.model.sqlalchemy import tag_def_parents_model, source_object_model, history_model, acl_org_model, acl_user_model
from app.services import exception_service
from app.model.pydantic.source_objects import tag_def_schema
from sqlalchemy import or_
from typing import Union
from app.services import config_service


def get_tag_by_name(tag_name: str, db: Session) -> source_object_model.TagDef:
    result = db.query(source_object_model.TagDef) \
        .filter(source_object_model.TagDef.name == tag_name) \
        .filter(source_object_model.TagDef.disabled_ts == None) \
        .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="tag {} not found".format(tag_name),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )


def get_val_tags(tag_name_parent: str, db: Session) -> list[str]:
    rs = db.query(source_object_model.TagDef) \
        .join(tag_def_parents_model.TagDefParents, source_object_model.TagDef.id == tag_def_parents_model.TagDefParents.tag_id) \
        .filter(tag_def_parents_model.TagDefParents.parent_ids.like("%{}%".format(tag_name_parent))) \
        .all()
    result = []
    for row in rs:
        result.append(row.name)
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="Cannot execute db query.",
                                      type="not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )


def get_tag_by_id(tag_id: int, db: Session, active=True) -> source_object_model.TagDef:
    result = db.query(source_object_model.TagDef) \
        .filter(source_object_model.TagDef.id == tag_id) \
        .filter(source_object_model.TagDef.disabled_ts == None) \
        .first() if active else \
        db.query(source_object_model.TagDef) \
            .filter(source_object_model.TagDef.id == tag_id) \
            .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="tag {} not found".format(tag_id),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )


def add_tag(db: Session, tag_def: tag_def_schema.TagDefCreate, user_id: int):
    db_tag_def = source_object_model.TagDef(
        url=tag_def.url,
        name=tag_def.name,
        base_uri=tag_def.base_uri,
        dis=tag_def.dis,
        doc=tag_def.doc,
        file_ext=tag_def.file_ext,
        max_val=tag_def.max_val,
        mime=tag_def.mime,
        min_val=tag_def.min_val,
        pref_unit=tag_def.pref_unit if tag_def.pref_unit is not None else [],
        version=tag_def.version
    )
    db.add(db_tag_def)
    db.flush()
    db.refresh(db_tag_def)
    add_tag_history(db, tag_def, db_tag_def.id, user_id)
    return db_tag_def


def update_tag(db: Session, tag_def: tag_def_schema.TagDefUpdate, tag_id: int, user_id: int):
    db_tag_def: tag_def_schema.TagDefBase = get_tag_by_id(tag_id, db)
    db_tag_def.name = tag_def.name
    db_tag_def.url = tag_def.url if tag_def.url is not None else None,
    db_tag_def.base_uri = tag_def.base_uri if tag_def.base_uri is not None else None,
    db_tag_def.dis = tag_def.dis if tag_def.dis is not None else None,
    db_tag_def.doc = tag_def.doc if tag_def.doc is not None else None,
    db_tag_def.file_ext = tag_def.file_ext if tag_def.file_ext is not None else None,
    db_tag_def.max_val = tag_def.max_val if tag_def.max_val is not None else None,
    db_tag_def.mime = tag_def.mime if tag_def.mime is not None else None,
    db_tag_def.min_val = tag_def.min_val if tag_def.min_val is not None else None,
    db_tag_def.pref_unit = tag_def.pref_unit if tag_def.pref_unit is not None else [],
    db_tag_def.version = tag_def.version if tag_def.version is not None else None
    add_tag_history(db, tag_def, tag_id, user_id)
    db.commit()
    return get_tag_by_id(tag_id, db)


def add_tag_history(db: Session, tag_def: tag_def_schema.TagDefBase, tag_id: int, user_id: int):
    db_tag_def_h = history_model.TagDefHistory(
        id=tag_id,
        name=tag_def.name,
        url=tag_def.url,
        base_uri=tag_def.base_uri,
        dis=tag_def.dis,
        doc=tag_def.doc,
        file_ext=tag_def.file_ext,
        max_val=tag_def.max_val,
        mime=tag_def.mime,
        min_val=tag_def.min_val,
        pref_unit=tag_def.pref_unit if tag_def.pref_unit is not None else [],
        version=tag_def.version,
        user_id=user_id,
        modified=datetime.now()
    )
    db.add(db_tag_def_h)


def delete_tag(db: Session, tag_def: tag_def_schema.TagDefDelete, tag_id: int, user_id: int):
    db_tag_def = get_tag_by_id(tag_id, db)
    db_tag_def.disabled_ts = datetime.now()
    return get_tag_by_id(tag_id, db, False)


def get_all(db: Session, user_id, org_id, name: Union[str, None], skip, limit):
    results = []

    if name is None:
        result = db.query(source_object_model.TagDef) \
            .filter(source_object_model.TagDef.id.in_(get_visible_tags_query(db, user_id, org_id))) \
            .offset(skip) \
            .limit(limit) \
            .all()
    else:
        result = db.query(source_object_model.TagDef) \
            .filter(source_object_model.TagDef.id.in_(get_visible_tags_query(db, user_id, org_id))) \
            .filter(source_object_model.TagDef.name.like("%{}%".format(name))) \
            .offset(skip) \
            .limit(limit) \
            .all()
    for res in result:
        return result
    return results


def get_visible_tags_query(db: Session, user_id: int, org_id: int):
    tag_def1 = aliased(source_object_model.TagDef)
    tag_def2 = aliased(source_object_model.TagDef)

    org_tag_permission_subquery = db.query(acl_org_model.OrgTagPermission) \
        .filter(acl_org_model.OrgTagPermission.org_id == org_id) \
        .filter(acl_org_model.OrgTagPermission.tag_id == source_object_model.TagMeta.value) \
        .exists()

    user_tag_add_permission_subquery = db.query(acl_user_model.UserTagAddPermission) \
        .filter(acl_user_model.UserTagAddPermission.user_id == user_id) \
        .filter(acl_user_model.UserTagAddPermission.tag_id == source_object_model.TagMeta.value) \
        .exists()

    user_tag_rev_permission_subquery = ~db.query(acl_user_model.UserTagRevPermission) \
        .filter(acl_user_model.UserTagRevPermission.user_id == user_id) \
        .filter(acl_user_model.UserTagRevPermission.tag_id == source_object_model.TagMeta.value) \
        .exists()

    subquery = db.query(source_object_model.TagMeta, acl_org_model.Org, acl_user_model.User) \
        .join(tag_def1, source_object_model.TagMeta.tag_id == tag_def1.id) \
        .join(tag_def2, source_object_model.TagMeta.attribute == tag_def2.id) \
        .filter(source_object_model.TagMeta.disabled_ts == None) \
        .filter(tag_def1.disabled_ts == None) \
        .filter(tag_def2.name == "lib") \
        .filter(acl_org_model.Org.id == org_id) \
        .filter(acl_user_model.User.id == user_id) \
        .filter(or_((org_tag_permission_subquery), (user_tag_add_permission_subquery))) \
        .filter(user_tag_rev_permission_subquery) \
        .with_entities(source_object_model.TagMeta.tag_id)
    return subquery


def get_tag(db: Session, tag_def_id: str):
    try:
        tag_id = int(tag_def_id)
    except:
        tag_id = get_tag_by_name(tag_def_id, db).id
    return tag_id
