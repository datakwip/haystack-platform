from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text
from app.model.sqlalchemy.base import Base
from app.services import config_service
from sqlalchemy.sql import func

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
        
    file_id = Column(String, primary_key=True, index=True)
    poller_id = Column(Integer, ForeignKey("{}.poller_config.poller_id".format(config_service.dbSchema)), nullable=False, index=True)
    raw_file_path = Column(String, nullable=False)
    processed_file_path = Column(String, nullable=True)
    created_time = Column(TIMESTAMP, nullable=True)
    processed_time = Column(TIMESTAMP, nullable=True)
    stored_time = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        {'schema': config_service.dbSchema}
    )