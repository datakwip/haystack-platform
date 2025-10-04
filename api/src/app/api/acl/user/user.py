from fastapi import Depends, HTTPException, Request
from app.model.pydantic.acl.user import user_schema
from app.model.pydantic.acl.org import org_user_schema
from app.dto.acl.user import user_dto
from app.dto.acl.org import org_dto
from sqlalchemy.orm import Session
from app.services import exception_service
import logging
import traceback
from app.services.acl import user_service

logger = logging.getLogger(__name__)
def init(app, get_db):
    @app.get("/user/org", response_model=list[org_user_schema.OrgUser])
    def read_orgs(request: Request,
                  skip: int = 0,
                  limit: int = 100,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_orgs = org_dto.get_current_user_orgs(db, user_id, skip=skip, limit=limit)
            return db_orgs
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.post("/user", response_model=user_schema.User)
    def create_user(user: user_schema.UserCreate,
                      request: Request,
                      db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_dto.create_user(db=db, user=user, user_id=user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/user", response_model=list[user_schema.User])
    def read_users(org_id : int,
                     request: Request,
                     skip: int = 0,
                     limit: int = 100,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            users = user_dto.get_users(db, org_id, user_id=user_id, skip=skip, limit=limit)
            return users
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/user/{user_id}", response_model=user_schema.User)
    def read_user(user_id: int,
                  org_id : int,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_object = user_dto.get_user(db, user_id, org_id = org_id, current_user_id=user_id)
            return db_object
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/user/{user_id}", response_model=user_schema.User)
    def delete_user(user_id: int,
                  user : user_schema.UserDelete,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return user_dto.delete_user(db, user=user, user_id=user_id, current_user_id=user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

