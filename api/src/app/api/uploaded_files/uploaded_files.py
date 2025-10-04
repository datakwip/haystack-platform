from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.model.pydantic.source_objects import uploaded_files_schema
from app.services import uploaded_files_service
from app.services.acl import app_user_service

def init(app, get_db):
    @app.post("/uploaded_file", response_model=uploaded_files_schema.UploadedFiles)
    def create_uploaded_file(
        request: Request,
        file_dict: uploaded_files_schema.UploadedFileCreate,
        db: Session = Depends(get_db)
    ):
        user_id = request.state.user_id
        if app_user_service.is_user_app_admin(db, user_id):
            return uploaded_files_service.create_uploaded_file(db, file_dict)

    @app.put("/uploaded_file/{file_id}", response_model=uploaded_files_schema.UploadedFiles)
    def update_uploaded_file(
        request: Request,
        file_id: str,
        file_update: uploaded_files_schema.UploadedFileUpdate,
        db: Session = Depends(get_db)
    ):
        user_id = request.state.user_id
        if app_user_service.is_user_app_admin(db, user_id):
            result = uploaded_files_service.update_uploaded_file(db, file_id, file_update)
            if result is None:
                raise HTTPException(status_code=404, detail="File not found")
            return result