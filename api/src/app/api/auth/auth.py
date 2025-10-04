from fastapi import Depends, HTTPException, Request
from app.services import exception_service
from app.services.auth import auth_service
import traceback
import logging
from app.model.pydantic.auth import auth_schema

logger = logging.getLogger(__name__)
def init(app):
    @app.post("/authorize/token", response_model=auth_schema.Token)
    def get_auth_token(  request: Request):
        try:
            user_id = request.state.user_id
            if "Authorization" in request.headers:
                auth_header = request.headers["Authorization"]
                if auth_header.startswith("Basic ") and len(auth_header) > 6:
                    return auth_service.getToken(auth_header[6:])
            raise exception_service.AccessDeniedException(
                exception_service.DtoExceptionObject(
                    [exception_service.Detail(msg="the client is not authorized to access the op",
                                              type="access.denied",
                                              loc=[])],
                    exception_service.Ctx("")
                )
            )

        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())

        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())
