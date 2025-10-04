from fastapi import Depends, HTTPException, Request
from app.model.pydantic.acl.user import user_entity_add_permission_schema
from app.dto.acl.user import user_entity_add_permission_dto
from sqlalchemy.orm import Session
from app.services import exception_service, request_service
import logging
import traceback
from app.services.acl import user_service

logger = logging.getLogger(__name__)
def init(app, get_db):
    @app.post("/userentityadd/", response_model=user_entity_add_permission_schema.UserEntityAddPermissions)
    def create_user(user_entity_add_permission: user_entity_add_permission_schema.UserEntityAddPermissionsCreate,
                      request: Request,
                      db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_entity_add_permission_dto.create_user_entity_add_permission(db=db, user_entity_add_permission=user_entity_add_permission, user_id=user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/userentityadd/", response_model=list[user_entity_add_permission_schema.UserEntityAddPermissions])
    def read_users(org_id : int,
                     request: Request,
                     skip: int = 0,
                     limit: int = 100,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_entity_add_permission_dto.get_user_entity_add_permissions(db, org_id, user_id=user_id, skip=skip, limit=limit)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/userentityadd/{user_entity_add_permission_id}", response_model=user_entity_add_permission_schema.UserEntityAddPermissions)
    def read_user(user_entity_add_permission_id: int,
                  org_id : int,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_entity_add_permission_dto.get_user_entity_add_permission(db, user_entity_add_permission_id, org_id = org_id, user_id=user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/userentityadd/{user_entity_add_permission_id}", response_model=user_entity_add_permission_schema.UserEntityAddPermissions)
    def delete_user(user_entity_add_permission_id: int,
                  user_entity_add_permission : user_entity_add_permission_schema.UserEntityAddPermissionsDelete,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_entity_add_permission_dto.delete_user_entity_add_permission(
                db,
                user_entity_add_permission=user_entity_add_permission,
                user_entity_add_permission_id=user_entity_add_permission_id,
                user_id=user_id
            )

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

