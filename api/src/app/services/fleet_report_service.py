import logging
import json
from sqlalchemy import text, literal_column, case
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.model.pydantic.source_objects import fleet_report_schema
from app.model.sqlalchemy.fleet_report_table import FleetReport
from app.services import config_service
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)

def get_org_schema_name(db: Session, org_id: int):
    try:
        sql = "SELECT schema_name FROM {}.org WHERE id = :org_id".format(config_service.dbSchema)
        result = db.execute(text(sql), {"org_id": org_id}).fetchone()
        return result[0] if result else None
    except SQLAlchemyError as e:
        logger.error(f"Error getting org schema name: {str(e)}")
        return None

def add_fleet_report(db: Session, report: fleet_report_schema.FleetReportCreate):
    try:
        schema_name = get_org_schema_name(db, report.org_id)
        if not schema_name:
            raise ValueError(f"Organization with ID {report.org_id} not found")

        sql = f"""
            INSERT INTO {schema_name}.fleet_report ("Device", "Network", "Status", "Attributes", "Onboarding_Date", "Last_Updated_Date")
            VALUES (:device, :network, :status, cast(:attributes as jsonb), :onboarded, :last_updated)
            ON CONFLICT ("Device", "Network") 
            DO UPDATE SET 
                "Status" = EXCLUDED."Status",
                "Attributes" = cast(:attributes as jsonb),
                "Onboarding_Date" = EXCLUDED."Onboarding_Date",
                "Last_Updated_Date" = EXCLUDED."Last_Updated_Date"     
        """
        
        params = {
            "device": report.device,
            "network": report.network,
            "status": report.status,
            "attributes": json.dumps(report.attributes) if report.attributes is not None else None,
            "onboarded": report.onboarded,
            "last_updated": report.last_updated
        }
        
        stmt = text(sql).bindparams(
            device=params["device"],
            network=params["network"],
            status=params["status"],
            attributes=params["attributes"],
            onboarded= params["onboarded"],
            last_updated= params["last_updated"]
        )
        
        db.execute(stmt)
        return report
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while adding fleet report: {str(e)}")
        raise
    
def add_bulk_fleet_report(db: Session, reports: fleet_report_schema.FleetReportBulkCreate):
    try:
        schema_name = get_org_schema_name(db, reports.org_id)
        if not schema_name:
            raise ValueError(f"Organization with ID {reports.org_id} not found")

        FleetReport.__table__.schema = schema_name

        db_reports = []
        for report in reports.reports:
            last_updated = report.last_updated if report.last_updated not in ("", None) else None
            db_reports.append({
                "Device": report.device,
                "Network": report.network,
                "Status": report.status,
                "Attributes": report.attributes,
                "Onboarding_Date": report.onboarded,
                "Last_Updated_Date": last_updated
            })
        
        stmt = pg_insert(FleetReport).values(db_reports)
        last_updated_case = case(
            [(stmt.excluded.Last_Updated_Date.isnot(None), stmt.excluded.Last_Updated_Date)],
            else_=FleetReport.Last_Updated_Date
        )
        update_dict = {
            "Status": stmt.excluded.Status,
            "Onboarding_Date": stmt.excluded.Onboarding_Date,
            "Last_Updated_Date": last_updated_case,
        }

        if any(r["Attributes"] != {} for r in db_reports):
            update_dict["Attributes"] = stmt.excluded.Attributes

        stmt = stmt.on_conflict_do_update(
            index_elements=["Device", "Network"],
            set_=update_dict
        )
        db.execute(stmt)
        
        return reports.reports
    except SQLAlchemyError as e:
        logger.error(f"Error occurred while adding bulk fleet reports: {str(e)}")
        raise