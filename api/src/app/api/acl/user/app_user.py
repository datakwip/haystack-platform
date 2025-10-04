from fastapi import Depends, HTTPException, Request
from app.model.pydantic.acl.user import app_user_schema
from app.dto.acl.user import app_user_dto
from sqlalchemy.orm import Session
from app.services import exception_service, request_service
import logging
import traceback
from app.services.acl import user_service

logger = logging.getLogger(__name__)
def init(app, get_db):
    @app.post("/appuser", response_model=app_user_schema.AppUser)
    def create_app_user(user: app_user_schema.AppUserCreate,
                      request: Request,
                      db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return app_user_dto.create_app_user(db=db, app_user=user, user_id=user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/appuser", response_model=list[app_user_schema.AppUser])
    def read_app_users(
            request: Request,
            skip: int = 0,
            limit: int = 100,
            db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            users = app_user_dto.get_app_users(db, user_id=user_id, skip=skip, limit=limit)
            return users
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/appuser/{app_user_id}", response_model=app_user_schema.AppUser)
    def read_app_user(app_user_id: int,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_app_user = app_user_dto.get_app_user(db, app_user_id=app_user_id, user_id=user_id)
            return db_app_user
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/appuser/{app_user_id}")
    def delete_app_user(app_user_id: int,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            app_user_dto.delete_app_user(db, app_user_id, user_id=user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

