import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from app.model.pydantic.filter import report_schema
from app.model.sqlalchemy import core_renu_table, core_ess_table

logger = logging.getLogger(__name__)


def add_devices_report(db: Session, req_filter: report_schema.RequestFilter):

    org = req_filter.org
    value = req_filter.value
    serial_number = value['serial_number']
    table = core_renu_table.tables['report'] if org == 'Renu' else core_ess_table.tables['report']

    db_value = {
        'Serial Number': value['serial_number'],
        'Site': None,
        'Space': None,
        'Organization': org.upper(),
        'Network': 'Enertech' if org == 'ESS' else 'Sense',
        'Present in Core': True,
        'Present in Old Model': False,
        'Present in Fleet Report': True,
        'Fleet Report Status': value['status'] or None,
        'Data Sharing Enabled': value['data_sharing_enabled'] or None
    }

    if org == 'Renu':
        sql = """
            SELECT p1.site_dis AS site, p1.space_dis AS space
            FROM core_renu.point p1
            WHERE p1."device_serialNumber" = :serial_number
        """
    else:
        sql = """
            SELECT p1."site_geoAddr" AS site, p1.device_type AS space
            FROM core_ess.point p1
            WHERE p1."device_serialNumber" = :serial_number
        """

    row = db.execute(text(sql), {'serial_number': serial_number}).first()

    try:
        try:
            site_addr, space_dis = row
            db_value.update(
                Site=site_addr,
                Network=space_dis if org == 'ESS' else 'Sense',
                Space=space_dis if org == 'Renu' else None
            )

        except Exception as e:
            logger.error("Can't destructure row object for: {} as it's not found in database \n error {}".format(
                serial_number, str(e)))

        stmt = insert(table).values(db_value)
        primary_key = [key.name for key in inspect(table).primary_key]

        stmt = stmt.on_conflict_do_update(
            index_elements=primary_key,
            set_={
                'Site': stmt.excluded['Site'],
                'Space': stmt.excluded["Space"],
                'Organization': stmt.excluded["Organization"],
                'Network': stmt.excluded['Network'],
                'Present in Core': stmt.excluded['Present in Core'],
                'Present in Old Model': stmt.excluded['Present in Old Model'],
                'Present in Fleet Report': stmt.excluded['Present in Fleet Report'],
                'Fleet Report Status': stmt.excluded['Fleet Report Status'],
                'Data Sharing Enabled': stmt.excluded['Data Sharing Enabled'],
            }
        )

        db.execute(stmt)
        return db_value
    except SQLAlchemyError as e:
        logger.error(
            "Error occurred while adding report: {}".format(str(e)))
        raise
