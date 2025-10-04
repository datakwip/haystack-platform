from sqlalchemy import Column, \
    ForeignKey, \
    Integer,\
    String,\
    TIMESTAMP, \
    UniqueConstraint
from app.model.sqlalchemy.base import Base
from app.services import config_service
from sqlalchemy.orm import relationship

class Org(Base):
    __tablename__ = "org"
    __table_args__ = {'schema': config_service.dbSchema}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    key = Column(String)
    value_table = Column(String, nullable=False)
    disabled_ts = Column(TIMESTAMP)
    schema_name = Column(String, nullable=False)

class OrgUser(Base):
    __tablename__ = "org_user"
    __table_args__ = {'schema': config_service.dbSchema}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("{}.org.id".format(config_service.dbSchema)), nullable=False, index=True)
    user = relationship(
        "User"
    )
    org = relationship(
        "Org"
    )

class OrgEntityPermission(Base):
    __tablename__ = "org_entity_permission"


    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("{}.org.id".format(config_service.dbSchema)), nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)), nullable=False, index=True)
    __table_args__ = (
        UniqueConstraint('org_id', 'entity_id'),
        {'schema': config_service.dbSchema},
    )



class OrgTagPermission(Base):
    __tablename__ = "org_tag_permission"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("{}.org.id".format(config_service.dbSchema)), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('org_id', 'tag_id'),
        {'schema': config_service.dbSchema},
    )
class OrgAdmin(Base):
    __tablename__ = "org_admin"


    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("{}.org.id".format(config_service.dbSchema)), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('org_id', 'user_id'),
        {'schema': config_service.dbSchema},
    )