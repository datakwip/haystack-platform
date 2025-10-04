from sqlalchemy.orm import Session

from app.model.sqlalchemy import tag_def_parents_model
from app.services import exception_service



def get_tag_parent_by_id(tag_id : int, db : Session) -> tag_def_parents_model.TagDefParents:
    result = db.query(tag_def_parents_model.TagDefParents) \
        .filter(tag_def_parents_model.TagDefParents.tag_id == tag_id)\
        .first()
    if result is not None:
        return result
    raise exception_service.BadRequestException(
        exception_service.DtoExceptionObject(
            [exception_service.Detail(msg="tag parent for tag {} not found".format(tag_id),
                                      type="value.not_found",
                                      loc=["body",
                                           "metas"])],
            exception_service.Ctx("")
        )
    )