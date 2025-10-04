from sqlalchemy.orm import Session

from app.model.pydantic.filter import report_schema
from app.services import fleet_devices_report_service


def create_report(db: Session, value : report_schema.RequestFilter, default_user_id : str):
    if default_user_id is not None:
        try:
            db_value = fleet_devices_report_service.add_devices_report(db,req_filter=value)
            db.commit()
            return db_value
        except Exception as e:
            db.rollback()
            raise e