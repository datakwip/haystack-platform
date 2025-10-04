from fastapi import Depends, HTTPException, Request
from app.model.pydantic.acl.org import org_schema
from app.dto.acl.org import org_dto
from sqlalchemy.orm import Session
from app.services import exception_service
from app.model.pydantic.acl.org import org_user_schema
import logging
import traceback

logger = logging.getLogger(__name__)
def init(app, get_db):
    @app.post("/org", response_model=org_schema.Org)
    def create_org(org: org_schema.OrgCreate,
                      request: Request,
                      db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return org_dto.create_org(db=db, org=org, user_id = user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.put("/org/{org_id}", response_model=org_schema.Org)
    def read_org(org_id: int,
                 org : org_schema.OrgUpdate,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_object = org_dto.update_org(db,  org, org_id=org_id, user_id = user_id)
            return db_object
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/org", response_model=list[org_schema.Org])
    def read_orgs(  request: Request,
                     skip: int = 0,
                     limit: int = 100,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_orgs = org_dto.get_orgs(db, user_id = user_id, skip=skip, limit=limit)
            return db_orgs
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())
        
    

    @app.get("/org/{org_id}", response_model=org_schema.Org)
    def update_org(org_id: int,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            db_object = org_dto.get_org(db, org_id = org_id, user_id = user_id)
            return db_object
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.delete("/org/{org_id}", response_model=org_schema.Org)
    def delete_org(org_id: int,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            return org_dto.delete_org(db, org_id=org_id, user_id = user_id)

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

    @app.get("/orgforcuruser", response_model=list[org_user_schema.OrgUser])
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
