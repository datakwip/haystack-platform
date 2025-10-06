"""
Test configuration and fixtures.

PREREQUISITES:
  1. Start databases: docker-compose up -d timescaledb statedb
  2. Run simulator to seed data: docker-compose up simulator

The simulator creates:
  - Organization (demo)
  - Tag definitions (site, equip, ahu, vav, point, temp, etc.)
  - Entities (site, AHUs, VAVs, points)
  - Time-series values

Tests use this existing data and create minimal additional entities.
"""

import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Database configuration
DATABASE_URL = "postgresql://datakwip_user:datakwip_password@localhost:5432/datakwip"

@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped database engine"""
    engine = create_engine(DATABASE_URL)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db(db_engine):
    """Function-scoped database session"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="session")
def client():
    """FastAPI test client (uses real database, not mocked)"""
    os.environ['CONFIG_PATH'] = './test/test_config.json'
    os.environ['dk_env'] = 'test'  # Use test config with localhost

    from app.main import app
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
def simulator_org(db_engine):
    """Get the organization created by simulator"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    result = session.execute(text("""
        SELECT id, name, key FROM core.org
        LIMIT 1
    """)).fetchone()

    session.close()

    if not result:
        pytest.fail("No organization found! Run simulator first: docker-compose up simulator")

    return {"id": result[0], "name": result[1], "key": result[2]}

@pytest.fixture(scope="session")
def simulator_entities(db_engine):
    """Get sample entities created by simulator"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Get a few sample entities
    result = session.execute(text("""
        SELECT e.id, e.value_table_id
        FROM core.entity e
        WHERE e.disabled_ts IS NULL
        LIMIT 5
    """)).fetchall()

    session.close()

    if not result:
        pytest.fail("No entities found! Run simulator first: docker-compose up simulator")

    return [{"id": row[0], "value_table_id": row[1]} for row in result]

@pytest.fixture(scope="session")
def simulator_tag_defs(db_engine):
    """Get tag definitions created by simulator"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    result = session.execute(text("""
        SELECT id, name FROM core.tag_def
        WHERE disabled_ts IS NULL
        LIMIT 10
    """)).fetchall()

    session.close()

    if not result:
        pytest.fail("No tag definitions found! Run simulator first: docker-compose up simulator")

    return [{"id": row[0], "name": row[1]} for row in result]

@pytest.fixture
def cleanup_entity(db):
    """Cleanup helper - yields entity ID to delete after test"""
    entity_ids_to_delete = []

    yield entity_ids_to_delete

    # Cleanup after test
    for entity_id in entity_ids_to_delete:
        db.execute(text("DELETE FROM core.entity_tag WHERE entity_id = :id"), {"id": entity_id})
        db.execute(text("DELETE FROM core.entity WHERE id = :id"), {"id": entity_id})
    db.commit()

@pytest.fixture
def auth_headers():
    """Generate test authentication headers (bypassed by local config)"""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }
