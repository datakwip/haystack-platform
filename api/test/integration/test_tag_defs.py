"""
Tag definition endpoint tests using simulator-generated data.

Tests use tag definitions created by the simulator service.
"""

import pytest


@pytest.mark.integration
def test_list_tag_defs(client, simulator_org):
    """Test GET /tagdef - List tag definitions from simulator"""
    response = client.get(f"/tagdef?org_id={simulator_org['id']}&limit=20")

    assert response.status_code == 200
    tag_defs = response.json()
    assert len(tag_defs) > 0, "Simulator should have created tag definitions"
    assert "id" in tag_defs[0]
    assert "name" in tag_defs[0]


@pytest.mark.integration
def test_get_tag_def_by_id(client, simulator_org, simulator_tag_defs):
    """Test GET /tagdef/{tag_id} - Get specific tag definition"""
    tag_def_id = simulator_tag_defs[0]["id"]

    response = client.get(f"/tagdef/{tag_def_id}?org_id={simulator_org['id']}")

    assert response.status_code == 200
    tag_def = response.json()
    assert tag_def["id"] == tag_def_id


@pytest.mark.integration
def test_list_tag_defs_pagination(client, simulator_org):
    """Test GET /tagdef - Pagination works"""
    response_page1 = client.get(
        f"/tagdef?org_id={simulator_org['id']}&skip=0&limit=5"
    )

    assert response_page1.status_code == 200
    page1_data = response_page1.json()
    assert isinstance(page1_data, list)
    assert len(page1_data) <= 5


@pytest.mark.integration
def test_filter_tag_defs_by_name(client, simulator_org):
    """Test GET /tagdef - Filter by name"""
    # Search for common tag like 'site'
    response = client.get(
        f"/tagdef?org_id={simulator_org['id']}&name=site"
    )

    assert response.status_code == 200
    tag_defs = response.json()
    assert isinstance(tag_defs, list)


@pytest.mark.integration
def test_get_tag_def_not_found(client, simulator_org):
    """Test GET /tagdef/{tag_id} - Returns 404 for non-existent tag"""
    response = client.get(
        f"/tagdef/nonexistent_tag_99999?org_id={simulator_org['id']}"
    )

    assert response.status_code in [400, 404]
