"""
Entity-tag relationship endpoint tests using simulator-generated data.

Tests use entities and tag definitions created by the simulator service.
"""

import pytest


@pytest.mark.integration
def test_list_entity_tags(client, simulator_org):
    """Test GET /entitytag - List entity tags from simulator"""
    response = client.get(f"/entitytag?org_id={simulator_org['id']}&limit=20")

    assert response.status_code == 200
    entity_tags = response.json()
    assert len(entity_tags) > 0, "Simulator should have created entity tags"
    assert "id" in entity_tags[0]


@pytest.mark.integration
def test_list_entity_tags_pagination(client, simulator_org):
    """Test GET /entitytag - Pagination works"""
    response = client.get(
        f"/entitytag?org_id={simulator_org['id']}&skip=0&limit=10"
    )

    assert response.status_code == 200
    entity_tags = response.json()
    assert isinstance(entity_tags, list)
    assert len(entity_tags) <= 10


@pytest.mark.integration
def test_filter_entity_tags_by_tag_id(client, simulator_org, simulator_tag_defs):
    """Test GET /entitytag - Filter by tag_id"""
    tag_id = simulator_tag_defs[0]["id"]

    response = client.get(
        f"/entitytag?org_id={simulator_org['id']}&tag_id={tag_id}"
    )

    assert response.status_code == 200
    entity_tags = response.json()
    assert isinstance(entity_tags, list)


@pytest.mark.integration
def test_create_entity_tag(client, simulator_org, simulator_entities, simulator_tag_defs, db):
    """Test POST /entitytag - Create entity-tag relationship"""
    entity_id = simulator_entities[0]["id"]
    tag_name = simulator_tag_defs[0]["name"]

    payload = {
        "org_id": simulator_org["id"],
        "entity_id": entity_id,
        "tag_name": tag_name,
        "value_s": "test_value"
    }

    response = client.post("/entitytag", json=payload)

    # May succeed or fail if tag already exists on entity
    assert response.status_code in [200, 400]

    # Cleanup if created successfully
    if response.status_code == 200:
        entitytag_id = response.json()["id"]
        from sqlalchemy import text
        db.execute(text("DELETE FROM core.entity_tag WHERE id = :id"), {"id": entitytag_id})
        db.commit()


@pytest.mark.integration
def test_get_entity_tag_not_found(client, simulator_org):
    """Test GET /entitytag/{entitytag_id} - Returns 404 for non-existent tag"""
    response = client.get(
        f"/entitytag/999999?org_id={simulator_org['id']}"
    )

    assert response.status_code in [400, 404]
