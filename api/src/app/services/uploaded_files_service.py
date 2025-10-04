import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from app.model.sqlalchemy.uploaded_files_table import UploadedFile
from app.model.pydantic.source_objects import uploaded_files_schema

logger = logging.getLogger(__name__)

def create_uploaded_file(db: Session, file_dict: uploaded_files_schema.UploadedFileCreate) -> uploaded_files_schema.UploadedFiles:
    db_file_dict = UploadedFile(
        file_id=file_dict.file_id,
        poller_id=file_dict.poller_id,
        raw_file_path=file_dict.raw_file_path,
        created_time=file_dict.created_time
    )
    
    db.add(db_file_dict)
    db.commit()
    db.refresh(db_file_dict)
    
    return _convert_to_schema(db_file_dict)

def update_uploaded_file(
    db: Session,
    file_id: str,
    file_update: uploaded_files_schema.UploadedFileUpdate
) -> uploaded_files_schema.UploadedFiles:
    db_file = db.query(UploadedFile).filter(UploadedFile.file_id == file_id).first()
    if not db_file:
        return None
    
    if file_update.processed_file_path is not None:
        db_file.processed_file_path = file_update.processed_file_path
    if file_update.processed_time is not None:
        db_file.processed_time = file_update.processed_time
    if file_update.stored_time is not None:
        db_file.stored_time = file_update.stored_time
    
    db.commit()
    db.refresh(db_file)
    return _convert_to_schema(db_file)

def _convert_to_schema(db_file_dict: UploadedFile) -> uploaded_files_schema.UploadedFiles:
    return uploaded_files_schema.UploadedFiles(
        file_id=db_file_dict.file_id,
        poller_id=db_file_dict.poller_id,
        raw_file_path=db_file_dict.raw_file_path,
        created_time=db_file_dict.created_time,
        processed_file_path=db_file_dict.processed_file_path,
        processed_time=db_file_dict.processed_time,
        stored_time=db_file_dict.stored_time
    )