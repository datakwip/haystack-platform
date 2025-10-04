from sqlalchemy import Boolean, \
    Column, \
    ForeignKey, \
    Integer,\
    String,\
    Numeric,\
    TIMESTAMP, \
    PrimaryKeyConstraint,\
    UniqueConstraint
from app.db.types._varchar import _Varchar
from app.model.sqlalchemy.base import Base
from app.db.types.jsonb import Jsonb
from app.services import config_service
class EntityTagHistory(Base):
    __tablename__ = "entity_tag_h"

    id = Column(Integer, ForeignKey("{}.entity_tag.id".format(config_service.dbSchema)), index=True)
    entity_id = Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)))
    tag_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)))
    value_n = Column(Numeric)
    value_b = Column(Boolean)
    value_s = Column(String)
    value_ts = Column(TIMESTAMP)
    value_list = Column(_Varchar)
    value_dict = Column(Jsonb)
    value_ref = Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)))
    value_enum = Column(Integer, ForeignKey("{}.tag_def_enum.id".format(config_service.dbSchema)))
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    modified = Column(TIMESTAMP)

    __table_args__ = (
        PrimaryKeyConstraint(id, modified),
        UniqueConstraint(entity_id, tag_id, modified),
        {'schema': config_service.dbSchema},
    )


class TagDefHistory(Base):
    __tablename__ = "tag_def_h"

    id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), index=True)
    name = Column(String, unique=False, index=True)
    url = Column(String)
    doc = Column(String)
    dis = Column(String)
    file_ext = Column(String)
    mime = Column(String)
    version = Column(String)
    min_val = Column(Integer)
    max_val = Column(Integer)
    base_uri = Column(String)
    pref_unit = Column(_Varchar)
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    modified = Column(TIMESTAMP)

    __table_args__ = (
        PrimaryKeyConstraint(id, modified),
        UniqueConstraint(name, modified),
        {'schema': config_service.dbSchema},
    )

class TagDefEnumHistory(Base):
    __tablename__ = "tag_def_enum_h"

    id = Column(Integer, ForeignKey("{}.tag_def_enum.id".format(config_service.dbSchema)), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False, index=True)
    value = Column(String, nullable=False)
    label = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    modified = Column(TIMESTAMP)

    __table_args__ = (
        PrimaryKeyConstraint(id, modified),
        UniqueConstraint(tag_id, value, modified),
        {'schema': config_service.dbSchema},
    )

class TagMetaHistory(Base):
    __tablename__ = "tag_meta_h"

    id = Column(Integer, ForeignKey("{}.tag_meta.id".format(config_service.dbSchema)), index=True)
    tag_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False,)
    attribute = Column(Integer, ForeignKey(
        "{}.tag_def.id".format(config_service.dbSchema)), nullable=False,)
    value = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)))
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    modified = Column(TIMESTAMP)
    __table_args__ = (
        UniqueConstraint(tag_id, attribute, value, modified),
        PrimaryKeyConstraint(id, modified),
        {'schema': config_service.dbSchema},
    )

class TagHierarchyHistory(Base):
    __tablename__ = "tag_hierarchy_h"

    id = Column(Integer,  ForeignKey("{}.tag_hierarchy.id".format(config_service.dbSchema)), index=True)
    child_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False)
    parent_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False)
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    modified = Column(TIMESTAMP)

    __table_args__ = (
        UniqueConstraint(child_id, parent_id, modified),
        PrimaryKeyConstraint(id, modified),
        {'schema': config_service.dbSchema},
    )

class EntityEnumHistory(Base):
    __tablename__ = "entity_enum_h"

    id = Column(Integer, ForeignKey("{}.entity_enum.id".format(config_service.dbSchema)), index=True)
    enum_id = Column(Integer)
    value = Column(String)
    label = Column(String)
    user_id = Column(Integer, ForeignKey("{}.user.id".format(config_service.dbSchema)), nullable=False, index=True)
    modified = Column(TIMESTAMP)

    __table_args__ = (
        PrimaryKeyConstraint(id, modified),
        UniqueConstraint(enum_id, value, modified),
        {'schema': config_service.dbSchema},
    )