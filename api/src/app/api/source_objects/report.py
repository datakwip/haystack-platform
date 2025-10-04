import json
import logging
import traceback
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request

from app.dto.source_objects import report_dto
from app.model.pydantic.filter import report_schema
from app.api.filter.antlr.antlr_error_listener import AntlrError

logger = logging.getLogger(__name__)

def init(app, get_db):
    @app.post("/report", response_model=report_schema.ReportBase)
    async def add_fleet_report_data(request: Request,
                                    db: Session = Depends(get_db)):
        try:
            filterDict = json.loads(await request.body())
            filter = report_schema.RequestFilter.parse_obj(filterDict)
            user_id = request.state.user_id
            default_user_id = request.state.default_user_id
            result = report_dto.create_report(db, filter, default_user_id)
            return {"message": "Fleet Report Successfully Added!"}

        except AntlrError as e:
            logger.error({"request_id": request.state.request_id,
                         "error_message": str(e)})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error({"request_id": request.state.request_id,
                         "error_message": str(e)})
            traceback.print_exc()
            raise e
