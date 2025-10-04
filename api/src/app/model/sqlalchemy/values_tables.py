from app.model.sqlalchemy.base import Base
from app.services.acl import org_service
from sqlalchemy.orm import Session
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

value_tables = {}
value_virtual_point_tables = {}
value_current_tables = {}
def getMapOfValueTables(db : Session):
    orgs = org_service.get_all(db, 0, 100000)
    created_tables = {}
    for org in orgs:
        if org.value_table not in created_tables.keys():
            attrs = {
                '__tablename__' : org.value_table,
                'entity_id' : Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)), index=True,
                              nullable=False),
                'ts' : Column(TIMESTAMP, server_default=func.now(), nullable=False),
                'value_n' : Column(Numeric),
                'value_b' : Column(Boolean),
                'value_s' : Column(String),
                'value_ts' : Column(TIMESTAMP),
                'value_dict' : Column(Jsonb),
                'status' : Column(String),
                '__table_args__' : (
                    PrimaryKeyConstraint('entity_id', 'ts'),
                    {'schema': config_service.dbSchema},
                )
                }
            value_tables[org.id] = type(org.value_table, (Base,), attrs)
            created_tables[org.value_table] = value_tables[org.id]
            attrs = {
                '__tablename__': "{}_current".format(org.value_table),
                'entity_id': Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)), index=True,
                                    nullable=False),
                'ts': Column(TIMESTAMP, server_default=func.now(), nullable=False),
                'value_n': Column(Numeric),
                'value_b': Column(Boolean),
                'value_s': Column(String),
                'value_ts': Column(TIMESTAMP),
                'value_dict': Column(Jsonb),
                'status': Column(String),
                '__table_args__': (
                    PrimaryKeyConstraint('entity_id'),
                    {'schema': config_service.dbSchema},
                )
            }
            value_current_tables[org.id] = type("{}_current".format(org.value_table), (Base,), attrs)
            created_tables["{}_current".format(org.value_table)] = value_current_tables[org.id]
            #attrs = {
            #    '__tablename__': "{}_virtual_points".format(org.value_table),
            #    'entity_id': Column(Integer, ForeignKey("{}.entity.id".format(config_service.dbSchema)), index=True,
            #                        nullable=False),
            #    'ts': Column(TIMESTAMP, server_default=func.now(), nullable=False),
            #    'value_n': Column(Numeric),
            #    'value_b': Column(Boolean),
            #    'value_s': Column(String),
            #    'value_ts': Column(TIMESTAMP),
            #    'status': Column(String),
            #    '__table_args__': (
            #        PrimaryKeyConstraint('entity_id', 'ts'),
            #        {'schema': config_service.dbSchema},
            #    )
            #}
            #value_virtual_point_tables[org.id] = type("{}_virtual_points".format(org.value_table), (Base,), attrs)
            #created_tables["{}_virtual_points".format(org.value_table)] = value_virtual_point_tables[org.id]
            i = 1
        else:
#            value_virtual_point_tables[org.id] = created_tables["{}_virtual_points".format(org.value_table)]
            value_tables[org.id] = created_tables[org.value_table]
            value_current_tables[org.id] = created_tables["{}_current".format(org.value_table)]