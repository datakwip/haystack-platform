from fastapi import Depends, HTTPException,Request
import traceback
from app.model.pydantic.source_objects import tag_def_schema, tag_def_enum_schema
from app.dto.source_objects import tag_def_dto, tag_enum_dto
from app.services import exception_service
from sqlalchemy.orm import Session
import logging
from typing import Union
from app.services.acl import org_service

logger = logging.getLogger(__name__)
def init(app, get_db):
    @app.post("/tagdef", response_model=tag_def_schema.TagDef)
    def create_tag_def(tag_def: tag_def_schema.TagDefCreate,
                       request: Request,
                       db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return tag_def_dto.create_tag_def(db=db, tag_def=tag_def, user_id = user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail= e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail= e.to_json())

    @app.get("/tagdef", response_model=list[tag_def_schema.TagDef])
    def read_tag_defs(request: Request,
                      org_id: int,
                      skip: int = 0,
                      limit: int = 100,
                      name: Union[str, None] = None,
                      db: Session = Depends(get_db),
                      ):
        try:
            user_id = request.state.user_id
            if org_service.is_org_visible_for_user(db, org_id=org_id, user_id=user_id):
                tag_defs = tag_def_dto.get_tag_defs(db, org_id, name, user_id = user_id, skip=skip, limit=limit)
                return tag_defs
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
            raise HTTPException(status_code=400, detail= e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail= e.to_json())

    @app.get("/tagdef/{tag_id}", response_model=tag_def_schema.TagDef)
    def read_tag_def(tag_id: str,
                     org_id: int,
                     request: Request,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_tagdef = tag_def_dto.get_tag_def(db, tag_def_id=tag_id, org_id = org_id, user_id = user_id)
            if db_tagdef is None:
                raise HTTPException(status_code=404, detail="Object not found")
            return db_tagdef
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail= e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail= e.to_json())

    @app.get("/tagdef/{tag_id}/enum/{value}", response_model=tag_def_enum_schema.TagDefEnum)
    def read_tag_def(tag_id: str,
                     value : str,
                     org_id: int,
                     request: Request,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_tagdef = tag_def_dto.get_tag_def(db, tag_def_id=tag_id, org_id=org_id, user_id = user_id)
            db_tagdef_enum = tag_enum_dto.get_tag_enum_by_value(db, db_tagdef.id, value)
            return db_tagdef_enum
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.put("/tagdef/{tag_id}", response_model=tag_def_schema.TagDef)
    def update_tag_def(tag_id : int,
                       tag_def: tag_def_schema.TagDefUpdate,
                       request: Request,
                       db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return tag_def_dto.update_tag_def(db=db, tag_def=tag_def, tag_id=tag_id, user_id = user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/tagdef/{tag_id}", response_model=tag_def_schema.TagDef)
    def delete_tag_def(tag_id: int,
                       tag_def : tag_def_schema.TagDefDelete,
                       request: Request,
                       db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return tag_def_dto.delete_tag_def(db=db, tag_def=tag_def, tag_id=tag_id, user_id = user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())