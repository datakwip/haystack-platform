from sqlalchemy.orm import Session
from app.model.pydantic.filter import value_schema
from app.services.acl import org_service
from app.services import config_service, exception_service, entity_tag_service
import logging
from app.model.sqlalchemy import values_tables
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.inspection import inspect
from app.model.sqlalchemy import dynamic_value_tables


logger = logging.getLogger(__name__)

test_table = config_service.test_table
orgs_with_value_dict = [1,2,3,5,6,7,8,9]
def add_value(db: Session, value: value_schema.ValueBaseCreate):
    if value.org_id in values_tables.value_tables:
        if not test_table:
            table = values_tables.value_tables[value.org_id]
        else:
            table = dynamic_value_tables.tables["value"]
        #if entity_tag_service.isEntityVirtualPoint(db, value.entity_id):
        #    table = values_tables.value_virtual_point_tables[value.org_id]
        db_value = {
            "ts": value.ts,
            "entity_id": value.entity_id,
            "value_n": value.value_n,
            "value_b": value.value_b,
            "value_s": value.value_s,
            "value_ts": value.value_ts,
        }
        if value.org_id not in orgs_with_value_dict:
            db_value = {
                    "ts":value.ts,
                    "entity_id":value.entity_id,
                    "value_n":value.value_n,
                    "value_b":value.value_b,
                    "value_s":value.value_s,
                    "value_ts":value.value_ts,
                    "value_dict": value.value_dict
            }

    else:
        logger.error("table for org {} not found. Available tables: {}".format(value.org_id, list(values_tables.value_tables.keys())))
        raise exception_service.AccessDeniedException(
            exception_service.DtoExceptionObject(
                [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                          loc=[])],
                exception_service.Ctx("")
            )
        )
    stmt = insert(table).values(db_value)
    primary_keys = [key.name for key in inspect(table).primary_key]
    if value.org_id not in orgs_with_value_dict:
        stmt = stmt.on_conflict_do_update(
            index_elements=primary_keys,
            set_={
                "value_n": stmt.excluded.value_n,
                "value_b": stmt.excluded.value_b,
                "value_s": stmt.excluded.value_s,
                "value_ts": stmt.excluded.value_ts,
                "value_dict": stmt.excluded.value_dict
            }
        )
    else:
        stmt = stmt.on_conflict_do_update(
            index_elements=primary_keys,
            set_={
                "value_n": stmt.excluded.value_n,
                "value_b": stmt.excluded.value_b,
                "value_s": stmt.excluded.value_s,
                "value_ts": stmt.excluded.value_ts,
            }
        )
    db.execute(stmt)
    #db.add(db_value)
    #db.flush()
    #db.refresh(db_value)
    return db_value

def add_bulk_value(db: Session, values: value_schema.ValueBulkCreate):
    if values.org_id in values_tables.value_tables:
        if not test_table:
            table = values_tables.value_tables[values.org_id]
        else:
            table = dynamic_value_tables.tables["value"]
        db_values = []
        for val in values.values:
            db_value = {
                "ts": val.ts,
                "entity_id": val.entity_id,
                "value_n": val.value_n,
                "value_b": val.value_b,
                "value_s": val.value_s,
                "value_ts": val.value_ts,
            }
            if values.org_id not in orgs_with_value_dict:
                db_value = {
                        "ts":val.ts,
                        "entity_id":val.entity_id,
                        "value_n":val.value_n,
                        "value_b":val.value_b,
                        "value_s":val.value_s,
                        "value_ts":val.value_ts,
                        "value_dict": val.value_dict
                }
            db_values.append(db_value)
    else:
        logger.error("table for org {} not found. Value in the database is {}".format(values.org_id, values_tables))
        raise exception_service.AccessDeniedException(
            exception_service.DtoExceptionObject(
                [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                          loc=[])],
                exception_service.Ctx("")
            )
        )
    stmt = insert(table).values(db_values)
    primary_keys = [key.name for key in inspect(table).primary_key]
    if values.org_id not in orgs_with_value_dict:
        stmt = stmt.on_conflict_do_update(
            index_elements=primary_keys,
            set_={
                "value_n": stmt.excluded.value_n,
                "value_b" : stmt.excluded.value_b,
                "value_s" : stmt.excluded.value_s,
                "value_ts" : stmt.excluded.value_ts,
                "value_dict": stmt.excluded.value_dict
            }
        )
    else:
        stmt = stmt.on_conflict_do_update(
            index_elements=primary_keys,
            set_={
                "value_n": stmt.excluded.value_n,
                "value_b": stmt.excluded.value_b,
                "value_s": stmt.excluded.value_s,
                "value_ts": stmt.excluded.value_ts,
            }
        )
    db.execute(stmt)
    #db.bulk_save_objects(db_values)
    return []

def add_bulk_value_current(db: Session, values: value_schema.ValueBulkCreate):
    if values.org_id in values_tables.value_current_tables:
        if not test_table:
            table = values_tables.value_current_tables[values.org_id]
        else:
            table = dynamic_value_tables.tables["value_current"]
        entity_map = {}

        for val in values.values:
            db_value = {
                "ts": val.ts,
                "entity_id": val.entity_id,
                "value_n": val.value_n,
                "value_b": val.value_b,
                "value_s": val.value_s,
                "value_ts": val.value_ts,
            }
            if values.org_id not in orgs_with_value_dict:
                db_value["value_dict"] = val.value_dict

            existing = entity_map.get(val.entity_id)

            # Only keep if newer, or first time seeing this entity_id
            if existing is None or val.ts > existing["ts"]:
                entity_map[val.entity_id] = db_value

        db_values = list(entity_map.values())
    else:
        logger.error("table for org {} not found. Value in the database is {}".format(values.org_id, values_tables))
        raise exception_service.AccessDeniedException(
            exception_service.DtoExceptionObject(
                [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                          loc=[])],
                exception_service.Ctx("")
            )
        )
    stmt = insert(table).values(db_values)
    primary_keys = [key.name for key in inspect(table).primary_key]
    if values.org_id not in orgs_with_value_dict:
        stmt = stmt.on_conflict_do_update(
            index_elements=primary_keys,
            set_={
                "ts": stmt.excluded.ts,
                "value_n": stmt.excluded.value_n,
                "value_b": stmt.excluded.value_b,
                "value_s": stmt.excluded.value_s,
                "value_ts": stmt.excluded.value_ts,
                "value_dict": stmt.excluded.value_dict,
            },
            where=(stmt.excluded.ts > table.ts)
        )
    else:
        stmt = stmt.on_conflict_do_update(
            index_elements=primary_keys,
            set_={
                "ts": stmt.excluded.ts,
                "value_n": stmt.excluded.value_n,
                "value_b": stmt.excluded.value_b,
                "value_s": stmt.excluded.value_s,
                "value_ts": stmt.excluded.value_ts,
            },
            where=(stmt.excluded.ts > table.ts)
        )
    db.execute(stmt)
    #db.bulk_save_objects(db_values)
    return []

def get_all_by_object(db: Session, org_id: int, object_id: int, skip: int, limit: int):
    """Get all values for a specific entity (object_id) using dynamic org table"""
    if org_id in values_tables.value_tables:
        table = values_tables.value_tables[org_id]
        results = []
        result = db.query(table)\
            .filter(table.entity_id == object_id)\
            .order_by(table.ts.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        if result is not None:
            return result
        return results
    else:
        raise exception_service.AccessDeniedException(
            exception_service.DtoExceptionObject(
                [exception_service.Detail(
                    msg="the client is not authorized to access the op",
                    type="access.denied",
                    loc=[])],
                exception_service.Ctx("")
            )
        )

def get_all_by_objects(db: Session, object_ids: list[int], date_from: str, date_to: str, org_id: int, skip: int , limit: int):
    if org_id in values_tables.value_tables:
        table = values_tables.value_tables[org_id]
        results = []
        result = db.query(table)\
            .filter(table.entity_id.in_(object_ids)) \
            .filter(table.ts > date_from) \
            .filter(table.ts < date_to) \
            .order_by(table.ts.desc()) \
            .offset(skip)\
            .limit(limit) \
            .all()
        if result is not None:
            return result
        return results
    else:
        raise exception_service.AccessDeniedException(
            exception_service.DtoExceptionObject(
                [exception_service.Detail(msg="the client is not authorized to access the op", type="access.denied",
                                          loc=[])],
                exception_service.Ctx("")
            )
        )

