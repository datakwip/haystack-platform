import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from app.model.sqlalchemy.poller_config_table import PollerConfig
from app.model.pydantic.source_objects import poller_config_schema

logger = logging.getLogger(__name__)

def get_poller_configs_by_org(db: Session, org_id: int) -> List[poller_config_schema.PollerConfig]:
    db_configs = db.query(PollerConfig).filter(
        PollerConfig.org_id == org_id,
        PollerConfig.status == "active"
    ).all()
    return [_convert_to_schema(config) for config in db_configs]

def get_poller_config_by_poller_id(db: Session, poller_id: int) -> poller_config_schema.PollerConfig:
    db_config = db.query(PollerConfig).filter(
        PollerConfig.poller_id == poller_id,
        PollerConfig.status == "active"
    ).first()
    if db_config:
        return _convert_to_schema(db_config)
    return None

def get_poller_configs_by_type(db: Session, poller_type: str) -> List[poller_config_schema.PollerConfig]:
    db_configs = db.query(PollerConfig).filter(
        PollerConfig.poller_type == poller_type,
        PollerConfig.status == "active"
    ).all()
    return [_convert_to_schema(config) for config in db_configs]

def create_poller_config(db: Session, config: poller_config_schema.PollerConfigCreate) -> poller_config_schema.PollerConfig:
    # Generate next available poller_id
    max_poller_id = db.query(PollerConfig.poller_id).order_by(PollerConfig.poller_id.desc()).first()
    next_poller_id = (max_poller_id[0] if max_poller_id else 0) + 1

    db_config = PollerConfig(
        org_id=config.org_id,
        poller_type=config.poller_type,
        poller_id=next_poller_id,
        poller_name=config.poller_name,
        config=config.config,
        status=config.status
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return _convert_to_schema(db_config)

def _convert_to_schema(db_config: PollerConfig) -> poller_config_schema.PollerConfig:
    return poller_config_schema.PollerConfig(
        id=db_config.id,
        org_id=db_config.org_id,
        poller_type=db_config.poller_type,
        poller_id=db_config.poller_id,
        poller_name=db_config.poller_name,
        config=db_config.config,
        status=db_config.status,
        created_at=db_config.created_at
    )