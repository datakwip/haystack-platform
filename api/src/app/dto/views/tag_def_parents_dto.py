from sqlalchemy.orm import Session
from app.services.acl import user_service
from app.services.views import tag_def_parents_service
from app.services import tag_def_service


def get_tag_def_parents(db: Session, tag_def_id: str, org_id: id, user_id : int):
    try:
        tag_id = int(tag_def_id)
    except:
        tag_id = tag_def_service.get_tag_by_name(tag_def_id, db).id
    if user_service.is_tag_visible_for_user(db, org_id, user_id, tag_id):
        return tag_def_parents_service.get_tag_parent_by_id(tag_id, db)

