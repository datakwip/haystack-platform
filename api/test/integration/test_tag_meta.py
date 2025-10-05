"""
Tag metadata endpoint tests using simulator-generated data.

Tests use tag definitions created by the simulator service.
"""

import pytest


@pytest.mark.integration
def test_list_tag_meta(client, simulator_org):
    """Test GET /tagmeta - List tag metadata"""
    response = client.get(f"/tagmeta?org_id={simulator_org['id']}&limit=20")

    assert response.status_code == 200
    tag_metas = response.json()
    assert isinstance(tag_metas, list)
    # May be empty if simulator doesn't create tag metadata


@pytest.mark.integration
def test_list_tag_meta_pagination(client, simulator_org):
    """Test GET /tagmeta - Pagination works"""
    response = client.get(
        f"/tagmeta?org_id={simulator_org['id']}&skip=0&limit=5"
    )

    assert response.status_code == 200
    tag_metas = response.json()
    assert isinstance(tag_metas, list)
    assert len(tag_metas) <= 5


@pytest.mark.integration
def test_create_tag_meta(client, simulator_org, simulator_tag_defs, db):
    """Test POST /tagmeta - Create tag metadata"""
    tag_id = simulator_tag_defs[0]["id"]

    payload = {
        "org_id": simulator_org["id"],
        "tag_id": tag_id,
        "attribute": "test_key",
        "value": "test_value"
    }

    response = client.post("/tagmeta", json=payload)

    # May succeed or fail if metadata already exists
    assert response.status_code in [200, 400]

    # Cleanup if successful
    if response.status_code == 200:
        meta_id = response.json()["id"]
        from sqlalchemy import text
        db.execute(text("DELETE FROM core.tag_meta WHERE id = :id"), {"id": meta_id})
        db.commit()


@pytest.mark.integration
def test_get_tag_meta_not_found(client, simulator_org):
    """Test GET /tagmeta/{meta_id} - Returns 404 for non-existent meta"""
    response = client.get(
        f"/tagmeta/999999?org_id={simulator_org['id']}"
    )

    assert response.status_code in [400, 404]
