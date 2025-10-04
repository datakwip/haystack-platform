from fastapi import Depends, HTTPException, Request
from app.model.pydantic.source_objects import entity_schema
from sqlalchemy.orm import Session
from app.services import exception_service
import logging
import traceback
from app.services.acl import user_service
from fastapi.responses import StreamingResponse
from app.services.export import export_service

logger = logging.getLogger(__name__)
def init(app, get_db):

    @app.get("/dbmodel", response_model=list[entity_schema.Entity])
    def read_entities(org_id : int,
                     request: Request,
                     skip: int = 0,
                     limit: int = 100,
                     db: Session = Depends(get_db)):
        try:
            user_id = request.state.user_id
            if user_service.is_user_org_admin(org_id, user_id, db):
                # Create a StreamingResponse
                output = export_service.export_data(org_id)
                response = StreamingResponse(output,
                                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                response.headers["Content-Disposition"] = "attachment; filename=data.xlsx"
                return response
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())

