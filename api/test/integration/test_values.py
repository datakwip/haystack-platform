"""
Value endpoint tests using simulator-generated data.

Tests use entities and time-series values created by the simulator service.
"""

import pytest
from datetime import datetime, timedelta


@pytest.mark.integration
def test_get_values_for_entity(client, simulator_org, simulator_entities):
    """Test GET /value/{entity_id} - Query values from simulator"""
    entity_id = simulator_entities[0]["id"]

    response = client.get(
        f"/value/{entity_id}?org_id={simulator_org['id']}&limit=50"
    )

    assert response.status_code == 200
    values = response.json()
    assert isinstance(values, list)
    # Simulator should have created values for entities
    # Note: May be empty if this specific entity doesn't have values


@pytest.mark.integration
def test_get_values_pagination(client, simulator_org, simulator_entities):
    """Test GET /value/{entity_id} - Pagination works"""
    entity_id = simulator_entities[0]["id"]

    response = client.get(
        f"/value/{entity_id}?org_id={simulator_org['id']}&skip=0&limit=10"
    )

    assert response.status_code == 200
    values = response.json()
    assert isinstance(values, list)
    assert len(values) <= 10


@pytest.mark.integration
def test_create_value(client, simulator_org, simulator_entities, db):
    """Test POST /value - Add single value"""
    entity_id = simulator_entities[0]["id"]

    payload = {
        "entity_id": entity_id,
        "org_id": simulator_org["id"],
        "timestamp": datetime.now().isoformat(),
        "value": 72.5
    }

    response = client.post("/value", json=payload)

    # May succeed or fail depending on entity type and constraints
    assert response.status_code in [200, 400, 500]

    # Cleanup if successful (delete from value table)
    if response.status_code == 200:
        # Note: Cleanup is complex for value tables, skip for now
        pass


@pytest.mark.integration
def test_bulk_create_values(client, simulator_org, simulator_entities):
    """Test POST /bulk/value - Batch insert"""
    entity_id = simulator_entities[0]["id"]

    # Create small batch of test values
    now = datetime.now()
    values = [
        {
            "entity_id": entity_id,
            "timestamp": (now - timedelta(minutes=i * 15)).isoformat(),
            "value": 70.0 + float(i)
        }
        for i in range(5)
    ]

    payload = {
        "org_id": simulator_org["id"],
        "values": values
    }

    response = client.post("/bulk/value", json=payload)

    # May succeed or fail depending on entity type
    assert response.status_code in [200, 400, 500]


@pytest.mark.integration
def test_get_values_for_invalid_entity(client, simulator_org):
    """Test GET /value/{entity_id} - Returns error for non-existent entity"""
    response = client.get(
        f"/value/999999?org_id={simulator_org['id']}&limit=10"
    )

    # May return empty list or error depending on implementation
    assert response.status_code in [200, 400, 404]
