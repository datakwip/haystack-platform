from fastapi import Depends, HTTPException, Request
from app.model.pydantic.filter import value_schema, filter_schema
from sqlalchemy.orm import Session
from app.api.filter.filter import filter_objects, get_values, get_variable_values
from app.api.filter.antlr.antlr_error_listener import AntlrError
from app.services.acl import user_service
import traceback
import json
import logging
from app.services.acl import user_service

logger = logging.getLogger(__name__)


def init(app, get_db):
    @app.post("/filter", response_model=list[filter_schema.FilterResponse])
    def get_filtered_points(filter: filter_schema.FilterRequest,
                            request: Request,
                            db: Session = Depends(get_db),
                            ):
        try:
            user_id = request.state.user_id
            return filter_objects(db=db, req_filter=filter, user=user_id)
        except AntlrError as e:
            logger.error({"request_id": request.state.request_id, "error_message": str(e)})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error({"request_id": request.state.request_id, "error_message": str(e)})
            traceback.print_exc()
            raise e

    @app.post("/values", response_model=list[value_schema.Value])
    async def get_values_for_filtered_points(request: Request,
                                             db: Session = Depends(get_db)):
        try:
            filterDict = json.loads(await request.body())

            filter = value_schema.ValueRequest.parse_obj(filterDict)

            user_id = request.state.user_id
            result = get_values(db=db, req_filter=filter, user=user_id)
            return result
        except AntlrError as e:
            logger.error({"request_id": request.state.request_id, "error_message": str(e)})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error({"request_id": request.state.request_id, "error_message": str(e)})
            traceback.print_exc()
            raise e

    @app.post("/variable/values", response_model=list[value_schema.VarValue])
    async def get_var_values(request: Request,
                             db: Session = Depends(get_db)):
        try:
            filter_dict = json.loads(await request.body())
            req_filter = value_schema.ValueRequest.parse_obj(filter_dict)
            user_id = request.state.user_id
            result = get_variable_values(db=db, req_filter=req_filter, user=user_id)
            return result
        except AntlrError as e:
            logger.error({"request_id": request.state.request_id, "error_message": str(e)})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error({"request_id": request.state.request_id, "error_message": str(e)})
            traceback.print_exc()
            raise e
