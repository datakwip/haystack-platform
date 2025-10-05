"""
Entity endpoint tests using simulator-generated data.

Tests use data created by the simulator service and create minimal
additional entities for POST/DELETE testing.
"""

import pytest


@pytest.mark.integration
def test_list_entities(client, simulator_org):
    """Test GET /entity - List entities created by simulator"""
    response = client.get(f"/entity?org_id={simulator_org['id']}&limit=10")

    assert response.status_code == 200
    entities = response.json()
    assert len(entities) > 0, "Simulator should have created entities"
    assert "id" in entities[0]


@pytest.mark.integration
def test_get_entity_by_id(client, simulator_org, simulator_entities):
    """Test GET /entity/{id} - Get specific entity from simulator"""
    entity_id = simulator_entities[0]["id"]

    response = client.get(f"/entity/{entity_id}?org_id={simulator_org['id']}")

    assert response.status_code == 200
    entity = response.json()
    assert entity["id"] == entity_id


@pytest.mark.integration
def test_create_entity(client, simulator_org, cleanup_entity):
    """Test POST /entity - Create new entity"""
    payload = {
        "org_id": simulator_org["id"],
        "tags": [
            {"tag_name": "site", "value_s": "Test Site"},
            {"tag_name": "area", "value_n": 5000}
        ]
    }

    response = client.post("/entity", json=payload)

    assert response.status_code == 200
    entity = response.json()
    assert "id" in entity

    # Register for cleanup
    cleanup_entity.append(entity["id"])


@pytest.mark.integration
def test_delete_entity(client, simulator_org, cleanup_entity):
    """Test DELETE /entity/{id}"""
    # First create an entity
    payload = {
        "org_id": simulator_org["id"],
        "tags": [{"tag_name": "site", "value_s": "Temp Site"}]
    }
    create_response = client.post("/entity", json=payload)
    entity_id = create_response.json()["id"]

    # Then delete it
    response = client.delete(
        f"/entity/{entity_id}",
        json={"org_id": simulator_org["id"]}
    )

    assert response.status_code == 200


@pytest.mark.integration
def test_list_entities_pagination(client, simulator_org):
    """Test GET /entity - Pagination works"""
    response_page1 = client.get(
        f"/entity?org_id={simulator_org['id']}&skip=0&limit=5"
    )

    assert response_page1.status_code == 200
    page1_data = response_page1.json()
    assert isinstance(page1_data, list)
    assert len(page1_data) <= 5


@pytest.mark.integration
def test_get_entity_not_found(client, simulator_org):
    """Test GET /entity/{id} - Returns 404 for non-existent entity"""
    response = client.get(
        f"/entity/999999?org_id={simulator_org['id']}"
    )

    assert response.status_code in [400, 404]
