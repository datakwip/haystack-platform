from app.model.sqlalchemy.base import Base
from sqlalchemy.orm import Session
from sqlalchemy import Boolean, \
    create_engine,\
    Column, \
    Text,\
    PrimaryKeyConstraint

from app.services.config_service import test_table

tables = {}
table_name = "sql_main_status_devices_renu" if not test_table else "test_sql_main_status_devices_renu"

def getMapOfCoreRenuTable(db: Session):
    serial_no_report_renu_attrs = {
        '__tablename__': table_name,
        '__table_args__': (
            PrimaryKeyConstraint('Serial Number'),
            {'schema': 'core_renu'},
        ),
        'Serial Number': Column(Text, primary_key=True, nullable=False, index=True),
        'Site': Column(Text),
        'Space': Column(Text),
        'Organization': Column(Text),
        'Network': Column(Text),
        'Present in Core': Column(Boolean),
        'Present in Old Model': Column(Boolean),
        'Present in Fleet Report': Column(Boolean),
        'Fleet Report Status': Column(Text),
        'Data Sharing Enabled': Column(Boolean),
    }

    serial_no_report_renu_table = type(
        table_name, (Base,), serial_no_report_renu_attrs)
    tables['report'] = serial_no_report_renu_table
