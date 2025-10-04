from fastapi import Depends, HTTPException, Request
from app.model.pydantic.acl.org import org_entity_permission_schema
from app.dto.acl.org import org_entity_permission_dto
from sqlalchemy.orm import Session
from app.services import exception_service, request_service
import logging
import traceback
from app.services.acl import user_service

logger = logging.getLogger(__name__)
def init(app, get_db):
    @app.post("/orgentity/", response_model=org_entity_permission_schema.OrgEntityPermission)
    def create_user(org_entity_permission: org_entity_permission_schema.OrgEntityPermissionCreate,
                      request: Request,
                      db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return org_entity_permission_dto.create_org_entity_permission(db=db, org_entity_permission=org_entity_permission, user_id=user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/orgentity/", response_model=list[org_entity_permission_schema.OrgEntityPermission])
    def read_users(  request: Request,
                     skip: int = 0,
                     limit: int = 100,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return org_entity_permission_dto.get_org_entity_permissions(db, user_id=user_id, skip=skip, limit=limit)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/orgentity/{org_entity_permission_id}", response_model=org_entity_permission_schema.OrgEntityPermission)
    def read_user(org_entity_permission_id: int,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return org_entity_permission_dto.get_org_entity_permission(db, org_entity_permission_id, user_id=user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/orgentity/{org_entity_permission_id}", response_model=org_entity_permission_schema.OrgEntityPermission)
    def delete_user(org_entity_permission_id: int,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return org_entity_permission_dto.delete_org_entity_permission(
                db,
                org_entity_permission_id,
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

