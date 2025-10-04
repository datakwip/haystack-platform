from sqlalchemy.orm import Session
from sqlalchemy import Boolean, \
    Column, \
    Text,\
    PrimaryKeyConstraint
    
from app.model.sqlalchemy.base import Base
from app.services.config_service import test_table

tables = {}
table_name = "sql_main_status_devices_ess" if not test_table else "test_sql_main_status_devices_ess"

def getMapOfCoreEssTable(db:Session):
    serial_no_report_ess_attrs = {
        '__tablename__': table_name,
        '__table_args__': (
            PrimaryKeyConstraint('Serial Number'),
            {'schema': 'core_ess'},
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

    serial_no_report_ess_table = type(
        table_name, (Base,), serial_no_report_ess_attrs)
    tables['report'] = serial_no_report_ess_table
