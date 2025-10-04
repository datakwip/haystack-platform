from sqlalchemy.orm import Session
from app.model.pydantic.source_objects import fleet_report_schema
from app.services import fleet_report_service, exception_service, config_service
from app.services.acl import user_service
import time
import logging

logger = logging.getLogger(__name__)

def create_fleet_report(db: Session, report: fleet_report_schema.FleetReportCreate):
    try:
        db_report = fleet_report_service.add_fleet_report(db, report)
        db.commit()
        return db_report
    except Exception as e:
        db.rollback()
        raise e
    
def create_bulk_fleet_report(db: Session, reports: fleet_report_schema.FleetReportBulkCreate):
    try:
        db_reports = fleet_report_service.add_bulk_fleet_report(db, reports)
        db.commit()
        return db_reports
    except Exception as e:
        db.rollback()
        raise e

def create_bulk_fleet_report_multi_db(all_databases: list, reports: fleet_report_schema.FleetReportBulkCreate, user_id: int, default_user_id: str):
    """Create bulk fleet reports in multiple databases"""
    # Use the first database for permission checks
    primary_db_config = next((db for db in all_databases if db.get('is_primary', False)), all_databases[0])
    primary_db = primary_db_config['database'].get_local_session()
    
    try:
        org_id = reports.org_id
        if default_user_id is not None or user_service.is_user_org_admin(org_id, user_id, primary_db):
            results = []
            successful_writes = 0
            
            for db_config in all_databases:
                db_session = db_config['database'].get_local_session()
                try:
                    if config_service.log_timing == '1':
                        st = time.time()
                    db_reports = fleet_report_service.add_bulk_fleet_report(db_session, reports)
                    db_session.commit()
                    
                    if config_service.log_timing == '1':
                        et = time.time()
                        elapsed_time = et - st
                        logger.info('Execution time of create_bulk_fleet_report for {}: {} seconds'.format(db_config['key'], elapsed_time))
                    
                    results.append(db_reports)
                    successful_writes += 1
                    logger.info(f"Successfully wrote bulk fleet reports to database {db_config['key']}")
                    
                except Exception as e:
                    db_session.rollback()
                    
                    if db_config.get('is_primary', False):
                        # Primary database failure - raise PrimaryDatabaseException
                        logger.error(f'Primary database {db_config["key"]} failed: {str(e)}')
                        raise exception_service.PrimaryDatabaseException(
                            f"Primary database {db_config['key']} failed during bulk fleet report creation", e)
                    else:
                        # Secondary database failure - log error but continue
                        logger.warning(f'Secondary database {db_config["key"]} failed: {str(e)}. Continuing with other databases.')
                        # Don't raise exception for secondary databases, just continue
                        
                finally:
                    db_session.close()
            
            logger.info(f"Bulk fleet reports successfully written to {successful_writes} out of {len(all_databases)} databases")
            return results[0] if results else []
            
    finally:
        primary_db.close()
    
    return []