from fastapi import Depends, HTTPException,Request
import logging
import traceback
from app.services import exception_service
from sqlalchemy.orm import Session
from app.model.pydantic.views import tag_def_parents_schema
from app.dto.views import tag_def_parents_dto
from app.services import tag_def_service

logger = logging.getLogger(__name__)


def init(app, get_db):

    @app.get("/tagdefparents", response_model=list[str])
    def read_tag_def(tag_parent_name: str, request: Request, db: Session = Depends(get_db)):
        try:
            return tag_def_service.get_val_tags(tag_parent_name, db)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())


    @app.get("/tagdefparents/{tag_id}", response_model=tag_def_parents_schema.TagDefParents)
    def read_tag_def(tag_id: str,
                         org_id: int,
                         request: Request,
                         db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_tagdef_parents = tag_def_parents_dto.get_tag_def_parents(db, tag_def_id=tag_id, org_id = org_id, user_id = user_id)
            if db_tagdef_parents is None:
                raise HTTPException(status_code=404, detail="Object not found")
            return db_tagdef_parents
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail= e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail= e.to_json())