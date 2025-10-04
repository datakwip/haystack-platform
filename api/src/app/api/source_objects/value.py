from fastapi import Depends, HTTPException,Request
import traceback
from app.model.pydantic.filter import value_schema
from app.dto.source_objects import value_dto
from app.services import exception_service
from sqlalchemy.orm import Session
import logging
from app.services.acl import user_service

logger = logging.getLogger(__name__)
def init(app, get_db):
    @app.post("/value", response_model=value_schema.ValueBase)
    def add_value(value: value_schema.ValueBaseCreate,
                       request: Request,
                       db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            default_user_id = request.state.default_user_id
            all_databases = request.state.all_databases
            return value_dto.create_value_multi_db(all_databases=all_databases, value=value, user_id=user_id, default_user_id=default_user_id)
        except exception_service.PrimaryDatabaseException as e:
            logger.error({"request_id": request.state.request_id, "detail": f"Primary database failure: {e.message}"})
            traceback.print_exc()
            # Return 503 Service Unavailable for primary database failures to signal poller to stop
            raise HTTPException(status_code=503, detail=f"Primary database unavailable: {e.message}")
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail= e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail= e.to_json())
        except Exception as e:
            if str(e) is not None and "psycopg2.errors.UniqueViolation" in str(e):
                logger.error({"request_id": request.state.request_id, "detail": str(e)})
            else:
                logger.error({"request_id": request.state.request_id, "detail": str(e)})
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/bulk/value", response_model=list[value_schema.ValueBase])
    def add_bulk_values(values: value_schema.ValueBulkCreate,
                       request: Request,
                       db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            default_user_id = request.state.default_user_id
            all_databases = request.state.all_databases
            return value_dto.create_bulk_value_multi_db(all_databases=all_databases, values=values, user_id=user_id, default_user_id=default_user_id)
        except exception_service.PrimaryDatabaseException as e:
            logger.error({"request_id": request.state.request_id, "detail": f"Primary database failure: {e.message}"})
            traceback.print_exc()
            # Return 503 Service Unavailable for primary database failures to signal poller to stop
            raise HTTPException(status_code=503, detail=f"Primary database unavailable: {e.message}")
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())
        except Exception as e:
            if str(e) is not None and "psycopg2.errors.UniqueViolation" in str(e):
                logger.error({"request_id": request.state.request_id, "detail": "org_id: {} error: {}".format(str(values.org_id), str(e))})
            else:
                logger.error({"request_id": request.state.request_id, "detail": "org_id: {} error: {}".format(str(values.org_id), str(e))})
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/value/{entity_id}", response_model=list[value_schema.ValueBase])
    def get_value_for_entity_id(request: Request,
                      entity_id: int,
                      org_id: int,
                      skip: int = 0,
                      limit: int = 100,
                      db: Session = Depends(get_db),
                      ):
        try:
            user_id = request.state.user_id
            db_value = value_dto.get_values_by_object(db, org_id, entity_id, user_id = user_id, skip=skip, limit=limit)
            return db_value
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail= e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail= e.to_json())
        except Exception as e:
            logger.error("super error")
            logger.error({"request_id": request.state.request_id, "detail": str(e)})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail= "not authorized")

    @app.post("/point/value", response_model=list[value_schema.ValueBaseResponse])
    def get_values_for_points(value: value_schema.ValueForPoints,
                  request: Request,
                  db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            default_user_id = request.state.default_user_id
            return value_dto.get_values_for_points(
                db=db , value=value, user_id=user_id)
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())
        except Exception as e:
            if str(e) is not None and "psycopg2.errors.UniqueViolation" in str(e):
                logger.error({"request_id": request.state.request_id, "detail": str(e)})
            else:
                logger.error({"request_id": request.state.request_id, "detail": str(e)})
