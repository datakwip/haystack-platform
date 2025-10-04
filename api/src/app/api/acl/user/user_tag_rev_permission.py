from fastapi import Depends, HTTPException, Request
from app.model.pydantic.acl.user import user_tag_rev_permission_schema
from app.dto.acl.user import user_tag_rev_permission_dto
from sqlalchemy.orm import Session
from app.services import exception_service
import logging
import traceback
from app.services.acl import user_service

logger = logging.getLogger(__name__)
def init(app, get_db):
    @app.post("/usertagrev/", response_model=user_tag_rev_permission_schema.UserTagRevPermissions)
    def create_user(user_tag_rev_permission: user_tag_rev_permission_schema.UserTagRevPermissionsCreate,
                      request: Request,
                      db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_tag_rev_permission_dto.create_user_tag_rev_permission(db=db, user_tag_rev_permission=user_tag_rev_permission, user_id=user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/usertagrev/", response_model=list[user_tag_rev_permission_schema.UserTagRevPermissions])
    def read_users(org_id : int,
                     request: Request,
                     skip: int = 0,
                     limit: int = 100,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_tag_rev_permission_dto.get_user_tag_rev_permissions(db, org_id, user_id=user_id, skip=skip, limit=limit)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/usertagrev/{user_tag_rev_permission_id}", response_model=user_tag_rev_permission_schema.UserTagRevPermissions)
    def read_user(user_tag_rev_permission_id: int,
                  org_id : int,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_tag_rev_permission_dto.get_user_tag_rev_permission(db, user_tag_rev_permission_id, org_id = org_id, user_id=user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/usertagrev/{user_tag_rev_permission_id}", response_model=user_tag_rev_permission_schema.UserTagRevPermissions)
    def delete_user(user_tag_rev_permission_id: int,
                  user_tag_rev_permission : user_tag_rev_permission_schema.UserTagRevPermissionsDelete,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_tag_rev_permission_dto.delete_user_tag_add_permission(
                db,
                user_tag_rev_permission=user_tag_rev_permission,
                user_tag_rev_permission_id=user_tag_rev_permission_id,
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
