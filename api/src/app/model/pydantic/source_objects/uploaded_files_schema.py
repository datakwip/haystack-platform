from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class UploadedFileCreate(BaseModel):
    file_id: UUID
    poller_id: int
    raw_file_path: str
    created_time: Optional[datetime] = None

class UploadedFileUpdate(BaseModel):
    processed_file_path: Optional[str] = None
    processed_time: Optional[datetime] = None
    stored_time: Optional[datetime] = None

class UploadedFiles(UploadedFileCreate):
    processed_file_path: Optional[str] = None
    processed_time: Optional[datetime] = None
    stored_time: Optional[datetime] = None

    class Config:
        orm_mode = True