"""
Integration tests for system endpoints.
"""

import pytest


@pytest.mark.integration
def test_health_check(client):
    """Test GET /health - Basic health check"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


@pytest.mark.integration
def test_database_health(client):
    """Test GET /health/databases - Database health check"""
    response = client.get("/health/databases")

    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "overall_status" in data
    assert "databases" in data
    assert "total_databases" in data
    assert "healthy_databases" in data

    # Validate status values
    assert data["overall_status"] in ["healthy", "degraded", "critical", "error"]

    # Validate databases array
    assert isinstance(data["databases"], list)

    if len(data["databases"]) > 0:
        db = data["databases"][0]
        assert "key" in db
        assert "status" in db
        assert db["status"] in ["healthy", "unhealthy", "unknown"]


@pytest.mark.integration
def test_health_endpoints_no_auth_required(client):
    """Test that health endpoints don't require authentication"""
    # Health endpoints should work without auth headers
    health_response = client.get("/health")
    assert health_response.status_code == 200

    db_health_response = client.get("/health/databases")
    assert db_health_response.status_code == 200
