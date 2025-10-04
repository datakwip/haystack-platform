from sqlalchemy.orm import Session
from app.model.pydantic.filter import value_schema
from app.services.acl import user_service
from app.services import value_service, config_service, util_service, exception_service
import time
import logging

logger = logging.getLogger(__name__)
def get_values_by_object(db: Session, org_id : int, object_id : int, user_id : int, skip: int = 0, limit: int = 100):
    if user_service.is_entity_visible_for_user(db, org_id, user_id, object_id):
        return value_service.get_all_by_object(db, object_id, skip, limit)



def get_values_for_points(db: Session, value: value_schema.ValueForPoints, user_id : int):
    limit = 1000 if value.limit > 1000 else value.limit
    skip = value.skip
    org_id = value.org_id
    date_from = value.date_from
    date_to = value.date_to
    if not util_service.is_valid_date_format(date_from):
        raise exception_service.BadRequestException(
            exception_service.DtoExceptionObject(
                [exception_service.Detail(msg="date_from should be in {} format".format(util_service.date_format),
                                          type="value.wrong_format",
                                          loc=["body"])],
                exception_service.Ctx("")
            )
        )
    if not util_service.is_valid_date_format(date_to):
        raise exception_service.BadRequestException(
            exception_service.DtoExceptionObject(
                [exception_service.Detail(msg="date_to should be in {} format".format(util_service.date_format),
                                          type="value.wrong_format",
                                          loc=["body"])],
                exception_service.Ctx("")
            )
        )
    if user_service.is_entities_visible_for_user(db, org_id, user_id, value.points):
        return value_service.get_all_by_objects(db, value.points, date_from, date_to, org_id, skip, limit)

def create_value(db: Session, value : value_schema.ValueBaseCreate, user_id : int, default_user_id : str):
    if default_user_id is not None or user_service.is_entity_visible_for_user(db, value.org_id, user_id, value.entity_id):
        try:
            db_value = value_service.add_value(db, value)
            db.commit()
            return db_value
        except Exception as e:
            db.rollback()
            raise e

def create_bulk_value(db: Session, values : value_schema.ValueBulkCreate, user_id : int, default_user_id : str):
    entity_ids = []
    for value in values.values:
        entity_ids.append(value.entity_id)
    if  default_user_id is not None or (len(entity_ids) > 0 and user_service.is_entities_visible_for_user(db, values.org_id, user_id, entity_ids)):
        try:
            if config_service.log_timing == '1':
                st = time.time()
            db_values = value_service.add_bulk_value(db, values)
            db_values_current =value_service.add_bulk_value_current(db, values)
            db.commit()
            if config_service.log_timing == '1':
                et = time.time()
                elapsed_time = et - st
                logger.info('Execution time of create_bulk_value: {} seconds'.format(elapsed_time))
            return db_values
        except Exception as e:
            db.rollback()
            raise e

def create_bulk_value_multi_db(all_databases: list, values: value_schema.ValueBulkCreate, user_id: int, default_user_id: str):
    """Create bulk values in multiple databases"""
    entity_ids = []
    for value in values.values:
        entity_ids.append(value.entity_id)
    
    # Use the first database for permission checks
    primary_db_config = next((db for db in all_databases if db.get('is_primary', False)), all_databases[0])
    primary_db = primary_db_config['database'].get_local_session()
    
    try:
        if default_user_id is not None or (len(entity_ids) > 0 and user_service.is_entities_visible_for_user(primary_db, values.org_id, user_id, entity_ids)):
            results = []
            successful_writes = 0
            
            for db_config in all_databases:
                db_session = db_config['database'].get_local_session()
                try:
                    if config_service.log_timing == '1':
                        st = time.time()
                    db_values = value_service.add_bulk_value(db_session, values)
                    db_values_current = value_service.add_bulk_value_current(db_session, values)
                    db_session.commit()
                    
                    if config_service.log_timing == '1':
                        et = time.time()
                        elapsed_time = et - st
                        logger.info('Execution time of create_bulk_value for {}: {} seconds'.format(db_config['key'], elapsed_time))
                    
                    results.append(db_values)
                    successful_writes += 1
                    logger.info(f"Successfully wrote bulk values to database {db_config['key']}")
                    
                except Exception as e:
                    db_session.rollback()
                    
                    if db_config.get('is_primary', False):
                        # Primary database failure - raise PrimaryDatabaseException
                        logger.error(f'Primary database {db_config["key"]} failed: {str(e)}')
                        raise exception_service.PrimaryDatabaseException(
                            f"Primary database {db_config['key']} failed during bulk value creation", e)
                    else:
                        # Secondary database failure - log error but continue
                        logger.warning(f'Secondary database {db_config["key"]} failed: {str(e)}. Continuing with other databases.')
                        # Don't raise exception for secondary databases, just continue
                        
                finally:
                    db_session.close()
            
            logger.info(f"Bulk values successfully written to {successful_writes} out of {len(all_databases)} databases")
            return results[0] if results else []
            
    finally:
        primary_db.close()
    
    return []

def create_value_multi_db(all_databases: list, value: value_schema.ValueBaseCreate, user_id: int, default_user_id: str):
    """Create value in multiple databases"""
    # Use the first database for permission checks
    primary_db_config = next((db for db in all_databases if db.get('is_primary', False)), all_databases[0])
    primary_db = primary_db_config['database'].get_local_session()
    
    try:
        if default_user_id is not None or user_service.is_entity_visible_for_user(primary_db, value.org_id, user_id, value.entity_id):
            results = []
            successful_writes = 0
            
            for db_config in all_databases:
                db_session = db_config['database'].get_local_session()
                try:
                    db_value = value_service.add_value(db_session, value)
                    db_session.commit()
                    results.append(db_value)
                    successful_writes += 1
                    logger.info(f"Successfully wrote value to database {db_config['key']}")
                    
                except Exception as e:
                    db_session.rollback()
                    
                    if db_config.get('is_primary', False):
                        # Primary database failure - raise PrimaryDatabaseException
                        logger.error(f'Primary database {db_config["key"]} failed: {str(e)}')
                        raise exception_service.PrimaryDatabaseException(
                            f"Primary database {db_config['key']} failed during value creation", e)
                    else:
                        # Secondary database failure - log error but continue
                        logger.warning(f'Secondary database {db_config["key"]} failed: {str(e)}. Continuing with other databases.')
                        # Don't raise exception for secondary databases, just continue
                        
                finally:
                    db_session.close()
            
            logger.info(f"Value successfully written to {successful_writes} out of {len(all_databases)} databases")
            return results[0] if results else None
            
    finally:
        primary_db.close()
    
    return None