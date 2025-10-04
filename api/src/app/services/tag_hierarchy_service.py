from sqlalchemy.orm import Session, aliased
from datetime import datetime
from app.model.sqlalchemy import aggregate_model, history_model, acl_org_model, acl_user_model
from app.services import exception_service
from app.model.sqlalchemy import source_object_model
from app.model.pydantic.source_objects import tag_meta_schema
from sqlalchemy.orm import Session
from app.services import tag_def_service
from app.model.pydantic.source_objects import tag_def_schema
from sqlalchemy import or_
from typing import Union

def get_tag_hierarchy_by_child_parent(db : Session, child_id : int, parent_id : int, active = True) -> aggregate_model.TagHierarchy:
    i = 2
    result = db.query(aggregate_model.TagHierarchy) \
        .filter(aggregate_model.TagHierarchy.child_id == child_id) \
        .filter(aggregate_model.TagHierarchy.parent_id == parent_id) \
        .filter(aggregate_model.TagHierarchy.disabled_ts == None) \
        .first() if active else \
        db.query(aggregate_model.TagHierarchy) \
            .filter(aggregate_model.TagHierarchy.child_id == child_id) \
            .filter(aggregate_model.TagHierarchy.parent_id == parent_id) \
            .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="hierarchy for child {} and parent {} not found".format(child_id, parent_id),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )
def add_tag_hierarchy_history(db: Session, history_id : int, child_id : int, parent_id : int, user_id : int):
    i = 2
    db_tag_hierarchy_h = history_model.TagHierarchyHistory(
        id = history_id,
        child_id=child_id,
        parent_id=parent_id,
        user_id=user_id,
        modified=datetime.now()
    )
    db.add(db_tag_hierarchy_h)
    db.flush()
    db.refresh(db_tag_hierarchy_h)

def add_tag_hierarchy(db: Session, child_id : int, parent_id : int, user_id : int):
    db_tag_history = aggregate_model.TagHierarchy(
        child_id=child_id,
        parent_id=parent_id,
    )
    db.add(db_tag_history)
    db.flush()
    db.refresh(db_tag_history)
    add_tag_hierarchy_history(db, db_tag_history.id, child_id, parent_id, user_id)
    return db_tag_history


def update_tag_hierarchy(db, current_meta: source_object_model.TagMeta, new_meta : tag_meta_schema.TagMetaUpdate, user_id):
    db_tag_hierarchy = get_tag_hierarchy_by_child_parent(db, current_meta.tag_id, current_meta.value)
    db_new_value = tag_def_service.get_tag_by_name(new_meta.value, db)
    db_tag_hierarchy.parent_id = db_new_value.id
    add_tag_hierarchy_history(db, db_tag_hierarchy.id , db_tag_hierarchy.child_id, db_new_value.id, user_id)
    return None