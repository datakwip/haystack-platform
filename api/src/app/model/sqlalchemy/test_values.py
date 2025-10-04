from app.model.sqlalchemy.base import Base
from sqlalchemy.orm import Session
from sqlalchemy import Boolean, \
    Column, \
    ForeignKey, \
    Integer,\
    String,\
    Numeric,\
    TIMESTAMP, \
    PrimaryKeyConstraint
from sqlalchemy import func
from app.services import config_service
from app.db.types.jsonb import Jsonb

tables = {}
def getMapOfTestValuesTable(db:Session):
    test_values_attrs = {
        '__tablename__': 'test_values',
        '__table_args__' : (
            PrimaryKeyConstraint('entity_id', 'ts'),
            {'schema': config_service.dbSchema},
        ),
        'entity_id' : Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)), index=True,
                        nullable=False),
        'ts' : Column(TIMESTAMP, server_default=func.now(), nullable=False),
        'value_n' : Column(Numeric),
        'value_b' : Column(Boolean),
        'value_s' : Column(String),
        'value_ts' : Column(TIMESTAMP),
        'value_dict' : Column(Jsonb),
        'status' : Column(String),
    }

    test_values_current_attrs = {
        '__tablename__': 'test_values_current',
        '__table_args__': (
            PrimaryKeyConstraint('entity_id'),
            {'schema': config_service.dbSchema},
        ),
        'entity_id': Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)), index=True,
                            nullable=False),
        'ts': Column(TIMESTAMP, server_default=func.now(), nullable=False),
        'value_n': Column(Numeric),
        'value_b': Column(Boolean),
        'value_s': Column(String),
        'value_ts': Column(TIMESTAMP),
        'value_dict': Column(Jsonb),
        'status': Column(String),
    }

    test_values_table = type(
        'test_values', (Base,), test_values_attrs)
    test_values_current_table = type(
        'test_values_current', (Base,), test_values_current_attrs)
    tables["value"] = test_values_table
    tables["value_current"] = test_values_current_table
