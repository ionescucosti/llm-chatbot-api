"""Tests for health check endpoint."""

from fastapi.testclient import TestClient


def test_get_health(client: TestClient):
    """Test GET /health returns OK status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"Health": "OK"}


def test_get_root(client: TestClient):
    """Test GET / returns Hello World."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}
