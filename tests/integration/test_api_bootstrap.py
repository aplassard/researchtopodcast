"""Test API bootstrap functionality."""

import pytest
from fastapi.testclient import TestClient
from researchtopodcast.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns Hello Audio!"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello Audio!"}


def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
