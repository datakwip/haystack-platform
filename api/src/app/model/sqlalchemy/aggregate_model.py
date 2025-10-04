from sqlalchemy import Boolean, \
    Column, \
    ForeignKey, \
    Integer,\
    UniqueConstraint,\
    TIMESTAMP
from app.model.sqlalchemy.base import Base
from app.services import config_service
class TagHierarchy(Base):
    __tablename__ = "tag_hierarchy"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False)
    parent_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False)
    disabled_ts = Column(TIMESTAMP)

    __table_args__ = (
        UniqueConstraint(child_id, parent_id),
        {'schema': config_service.dbSchema},
    )