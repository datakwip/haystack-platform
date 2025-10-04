from sqlalchemy import Boolean, \
    Column, \
    ForeignKey, \
    Integer,\
    String,\
    Numeric,\
    TIMESTAMP, \
    UniqueConstraint, \
    PrimaryKeyConstraint
from app.db.types._varchar import _Varchar
from sqlalchemy.orm import relationship
from app.model.sqlalchemy.base import Base
from sqlalchemy import func
from app.services import config_service
from app.db.types.jsonb import Jsonb

class Entity(Base):
    __tablename__ = "entity"
    __table_args__ = {'schema': config_service.dbSchema}

    id = Column(Integer, primary_key=True, index=True)
    value_table_id = Column(String)
    disabled_ts = Column(TIMESTAMP)

    tags = relationship(
        "EntityTag", foreign_keys='EntityTag.entity_id'
    )

class TagDef(Base):
    __tablename__ = "tag_def"
    __table_args__ = {'schema': config_service.dbSchema}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
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
    disabled_ts = Column(TIMESTAMP)
    metas = relationship(
        "TagMeta", foreign_keys='TagMeta.tag_id'
    )
    enums = relationship(
        "TagDefEnum", foreign_keys='TagDefEnum.tag_id'
    )


class TagDefEnum(Base):
    __tablename__ = "tag_def_enum"

    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False, index=True)
    value = Column(String, nullable=False)
    label = Column(String, nullable=False)
    disabled_ts = Column(TIMESTAMP)
    __table_args__ = (
        UniqueConstraint(tag_id, value),
        {'schema': config_service.dbSchema},
    )

class TagMeta(Base):
    __tablename__ = "tag_meta"

    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), nullable=False)
    attribute = Column(Integer, ForeignKey(
        "{}.tag_def.id".format(config_service.dbSchema)), nullable=False,)
    value = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)))
    disabled_ts = Column(TIMESTAMP)
    __table_args__ = (
        UniqueConstraint('tag_id', 'attribute', 'value'),
        {'schema': config_service.dbSchema},
    )

class EntityTag(Base):
    __tablename__ = "entity_tag"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)), index=True)
    tag_id = Column(Integer, ForeignKey("{}.tag_def.id".format(config_service.dbSchema)), index=True)
    value_n = Column(Numeric)
    value_b = Column(Boolean)
    value_s = Column(String)
    value_ts = Column(TIMESTAMP)
    value_list = Column(_Varchar)
    value_dict = Column(Jsonb)
    value_ref = Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)))
    value_enum = Column(Integer, ForeignKey("{}.tag_def_enum.id".format(config_service.dbSchema)))
    disabled_ts = Column(TIMESTAMP)
    __table_args__ = (
        UniqueConstraint(entity_id, tag_id, disabled_ts),
        {'schema': config_service.dbSchema},
    )

    tag = relationship(
        "TagDef"
    )

    @classmethod
    def get_all_column_names(cls):
        excluded_columns = ['id', 'entity_id', 'value_list', 'value_dict', 'disabled_ts']
        return [column.name for column in cls.__table__.columns if column.name not in excluded_columns]

class EntityEnum(Base):
    __tablename__ = "entity_enum"

    id = Column(Integer, primary_key=True, index=True)
    enum_id = Column(Integer)
    value = Column(String)
    label = Column(String)
    disabled_ts = Column(TIMESTAMP)
    __table_args__ = (
        UniqueConstraint(enum_id, value),
        {'schema': config_service.dbSchema},
    )


class EntityEnumDef(Base):
    __tablename__ = "entity_enum_def"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    __table_args__ = (
        UniqueConstraint(name),
        {'schema': config_service.dbSchema},
    )

