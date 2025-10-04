from fastapi import Depends, Request, HTTPException
from app.model.pydantic.source_objects import entity_tag_schema
from app.dto.source_objects import entity_tag_dto
from sqlalchemy.orm import Session
from app.services import exception_service
from app.services.acl import org_service
import logging
import traceback
from app.services.acl import user_service

logger = logging.getLogger(__name__)
def init(app, get_db):
    @app.post("/entitytag", response_model=entity_tag_schema.EntityTag)
    def create_entity_tag_relationship(
            entity_tag: entity_tag_schema.EntityTagCreateWithEntityId,
            request: Request,
            db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return entity_tag_dto.create_entity_tag(
                db=db,
                entity_tag=entity_tag,
                user_id=user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/entitytag", response_model=list[entity_tag_schema.EntityTag])
    def read_entity_tags( request: Request,
                                      org_id: int,
                                      tag_id : str = None,
                                      value_s : str = None,
                                      skip: int = 0,
                                      limit: int = 100,
                                      db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            if org_service.is_org_visible_for_user(db, org_id=org_id, user_id = user_id):
                entity_tag = entity_tag_dto.get_entity_tags(
                    db, org_id, tag_id, value_s, user_id=user_id, skip=skip, limit=limit)
                return entity_tag
            raise exception_service.AccessDeniedException(
                exception_service.DtoExceptionObject(
                    [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                              loc=[])],
                    exception_service.Ctx("")
                )
            )
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/entitytag/{entitytag_id}", response_model=entity_tag_schema.EntityTag)
    def read_entity_tag(entitytag_id : int,
                                      request: Request,
                                      org_id: int,
                                      db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_entity_tag = entity_tag_dto.get_entity_tag(db, entitytag_id=entitytag_id, org_id=org_id, user_id=user_id)
            return db_entity_tag

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.put("/entitytag/{entitytag_id}", response_model=entity_tag_schema.EntityTag)
    def update_entity_tag(entitytag_id: int,
                       entity_tag: entity_tag_schema.EntityTagUpdate,
                       request: Request,
                       db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return entity_tag_dto.update_entity_tag(
                db=db,
                entity_tag = entity_tag,
                entitytag_id=entitytag_id,
                user_id=user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/entitytag/{entitytag_id}", response_model=entity_tag_schema.EntityTag)
    def delete_entity_tag(entitytag_id: int,
                  entity_tag: entity_tag_schema.EntityTagDelete,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return entity_tag_dto.delete_entity_tag(
                db,
                entity_tag=entity_tag,
                entitytag_id=entitytag_id,
                user_id=user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())


