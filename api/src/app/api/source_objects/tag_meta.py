from fastapi import Depends, HTTPException, Request
from app.model.pydantic.source_objects import tag_meta_schema
from app.dto.source_objects import tag_meta_dto
from sqlalchemy.orm import Session
import logging
from app.services import exception_service
import traceback
from app.services.acl import user_service

logger = logging.getLogger(__name__)

def init(app, get_db):
    @app.post("/tagmeta", response_model=tag_meta_schema.TagMeta)
    def create_tag_meta(tag_meta: tag_meta_schema.TagMetaCreate,
                        request: Request,
                        db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return tag_meta_dto.create_tag_meta(db=db, tag_meta=tag_meta, user_id = user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.put("/tagmeta/{meta_id}", response_model=tag_meta_schema.TagMeta)
    def update_tag_meta(tag_meta: tag_meta_schema.TagMetaUpdate,
                        meta_id: int,
                        request: Request,
                        db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return tag_meta_dto.update_tag_meta(db=db, tag_meta=tag_meta, meta_id = meta_id, user_id = user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/tagmeta/{meta_id}", response_model=tag_meta_schema.TagMeta)
    def delete_tag_meta(tag_meta: tag_meta_schema.TagMetaDelete,
                        meta_id: int,
                        request: Request,
                        db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return tag_meta_dto.delete_tag_meta(db=db, tag_meta=tag_meta, meta_id=meta_id, user_id = user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/tagmeta", response_model=list[tag_meta_schema.TagMeta])
    def read_tag_metas(org_id : int,
                       request: Request,
                       skip: int = 0,
                       limit: int = 100,
                       db: Session = Depends(get_db)):
        user_id = request.state.user_id
        tag_metas = tag_meta_dto.get_tag_metas(db, org_id, user_id = user_id, skip=skip, limit=limit)
        return tag_metas

    @app.get("/tagmeta/{meta_id}", response_model=tag_meta_schema.TagMeta)
    def read_tag_meta(meta_id: int,
                     org_id: int,
                     request: Request,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_tagdef = tag_meta_dto.get_meta_def(db, meta_id=meta_id, org_id = org_id, user_id = user_id)
            if db_tagdef is None:
                raise HTTPException(status_code=404, detail="Object not found")
            return db_tagdef
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())
