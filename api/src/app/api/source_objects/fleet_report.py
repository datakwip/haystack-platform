from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
import logging
import traceback
from typing import List
from app.model.pydantic.source_objects import fleet_report_schema
from app.dto.source_objects import fleet_report_dto
from app.services import exception_service
from app.services.acl import user_service

logger = logging.getLogger(__name__)

def init(app, get_db):
    @app.post("/fleet_report", response_model=fleet_report_schema.FleetReport)
    def create_fleet_report(
        report: fleet_report_schema.FleetReportCreate,
        request: Request,
        db: Session = Depends(get_db)
    ):
        try:
            user_id = request.state.user_id
            org_id = report.org_id
            if user_service.is_user_org_admin(org_id, user_id, db):
                return fleet_report_dto.create_fleet_report(db=db, report=report)
        except exception_service.BadRequestException as e:
            logger.error({"detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except Exception as e:
            logger.error({"detail": str(e)})
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
        
    @app.post("/bulk/fleet_report", response_model=List[fleet_report_schema.FleetReportBulkItem])
    def create_bulk_fleet_report(
        reports: fleet_report_schema.FleetReportBulkCreate,
        request: Request,
        db: Session = Depends(get_db)
    ):
        try:
            user_id = request.state.user_id
            default_user_id = request.state.default_user_id
            all_databases = request.state.all_databases
            org_id = reports.org_id
            if user_service.is_user_org_admin(org_id, user_id, db):
                logger.info(f"Received bulk fleet report request")
                logger.info(f"Number of reports: {len(reports.reports)}")
                
                result = fleet_report_dto.create_bulk_fleet_report_multi_db(all_databases=all_databases, reports=reports, user_id=user_id, default_user_id=default_user_id)
                
                logger.info(f"Successfully processed {len(result)} fleet reports")
                return result
            
        except exception_service.PrimaryDatabaseException as e:
            logger.error({"request_id": request.state.request_id, "detail": f"Primary database failure: {e.message}"})
            traceback.print_exc()
            raise HTTPException(status_code=503, detail=f"Primary database unavailable: {e.message}")
        except exception_service.BadRequestException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=e.to_json())
        except exception_service.AccessDeniedException as e:
            logger.error({"request_id": request.state.request_id, "detail": e.to_json()})
            traceback.print_exc()
            raise HTTPException(status_code=403, detail=e.to_json())
        except Exception as e:
            logger.error({"request_id": request.state.request_id, "detail": str(e)})
            logger.error(f"Request data: {reports.dict() if reports else 'No data'}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Internal server error")