from fastapi import Depends, HTTPException, Request
from app.model.pydantic.source_objects import tag_def_enum_schema
from app.dto.source_objects import tag_enum_dto
from sqlalchemy.orm import Session
import logging
from app.services import exception_service
import traceback
from app.services.acl import user_service

logger = logging.getLogger(__name__)

def init(app, get_db):
    @app.post("/tagenum/", response_model=tag_def_enum_schema.TagDefEnum)
    def create_tag_enum(tag_enum: tag_def_enum_schema.TagDefEnumCreate,
                        request: Request,
                        db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return tag_enum_dto.create_tag_enum(db, tag_enum, user_id=user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.put("/tagenum/{enum_id}", response_model=tag_def_enum_schema.TagDefEnum)
    def update_tag_enum(tag_enum: tag_def_enum_schema.TagDefEnumUpdate,
                        enum_id: int,
                        request: Request,
                        db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return tag_enum_dto.update_tag_enum(db=db, tag_enum=tag_enum, enum_id = enum_id, user_id=user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/tagenum/{enum_id}", response_model=tag_def_enum_schema.TagDefEnum)
    def update_tag_enums(tag_enum: tag_def_enum_schema.TagDefEnumDelete,
                        enum_id: int,
                        request: Request,
                        db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return tag_enum_dto.delete_tag_enum(db=db, tag_enum=tag_enum, enum_id=enum_id, user_id=user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/tagenum/", response_model=list[tag_def_enum_schema.TagDefEnum])
    def read_tag_metas(org_id : int,
                       request: Request,
                       skip: int = 0,
                       limit: int = 100,
                       db: Session = Depends(get_db)):
        user_id = request.state.user_id
        tag_enums = tag_enum_dto.get_tag_enums(db, org_id, user_id=user_id, skip=skip, limit=limit)
        return tag_enums

    @app.get("/tagenum/{tag_id}", response_model=list[tag_def_enum_schema.TagDefEnum])
    def read_tag_metas(org_id: int,
                       request: Request,
                       tag_id: int,
                       skip: int = 0,
                       limit: int = 100,
                       db: Session = Depends(get_db)):
        user_id = request.state.user_id
        tag_enums = tag_enum_dto.get_enum_for_tag(db, org_id, user_id=user_id, tag_id=tag_id, skip=skip, limit=limit)
        return tag_enums

    @app.get("/tagenum/{enum_id}", response_model=tag_def_enum_schema.TagDefEnum)
    def read_tag_enum(enum_id: int,
                     org_id: int,
                     request: Request,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_tagdef = tag_enum_dto.get_tag_def_enum(db, enum_id=enum_id, org_id = org_id, user_id=user_id)
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
