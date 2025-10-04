from sqlalchemy import Column, \
    ForeignKey, \
    Integer,\
    String,\
    TIMESTAMP, \
    UniqueConstraint
from app.model.sqlalchemy.base import Base
from sqlalchemy.orm import relationship
from app.services import config_service


class User(Base):
    __tablename__ = "user"
    __table_args__ = {'schema': config_service.dbSchema}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    disabled_ts = Column(TIMESTAMP)

    visible_entities = relationship(
        "UserEntityAddPermission"
    )
    invisible_entities = relationship(
        "UserEntityRevPermission"
    )
    visible_tags = relationship(
        "UserTagAddPermission"
    )
    invisible_tags = relationship(
        "UserTagRevPermission"
    )


class UserEntityAddPermission(Base):
    __tablename__ = "user_entity_add_permission"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,  ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    entity_id = Column(Integer,ForeignKey("{}.entity.id".format(config_service.dbSchema)), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'entity_id'),
        {'schema': config_service.dbSchema},
    )

class UserTagAddPermission(Base):
    __tablename__ = "user_tag_add_permission"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'tag_id'),
        {'schema': config_service.dbSchema},
    )
class UserEntityRevPermission(Base):
    __tablename__ = "user_entity_rev_permission"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,  ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    entity_id = Column(Integer,ForeignKey("{}.entity.id".format(config_service.dbSchema)), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'entity_id'),
        {'schema': config_service.dbSchema},
    )

class UserTagRevPermission(Base):
    __tablename__ = "user_tag_rev_permission"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'tag_id'),
        {'schema': config_service.dbSchema},
    )

class AppUser(Base):
    __tablename__ = "user_app"
    __table_args__ = {'schema': config_service.dbSchema}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)

    user = relationship(
        "User"
    )