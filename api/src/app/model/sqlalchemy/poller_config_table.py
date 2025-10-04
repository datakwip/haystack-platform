from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text
from app.model.sqlalchemy.base import Base
from app.services import config_service
from sqlalchemy.sql import func

class PollerConfig(Base):
    __tablename__ = "poller_config"
        
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("{}.org.id".format(config_service.dbSchema)), nullable=False, index=True)
    poller_type = Column(String, nullable=False)
    poller_id = Column(Integer, nullable=False, unique=True)
    poller_name = Column(String, nullable=False)
    config = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('NOW()'))

    __table_args__ = (
        {'schema': config_service.dbSchema}
    )