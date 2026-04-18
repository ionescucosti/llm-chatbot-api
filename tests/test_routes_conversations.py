"""Tests for conversation endpoints."""

from fastapi.testclient import TestClient


def test_create_conversation(client: TestClient):
    """Test POST /conversations creates a new conversation."""
    response = client.post(
        "/conversations/",
        json={"conversation_title": "Test Conversation"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["conversation_title"] == "Test Conversation"


def test_create_conversation_duplicate_title(client: TestClient):
    """Test POST /conversations returns 409 for duplicate title."""
    # Create first conversation
    client.post("/conversations/", json={"conversation_title": "Duplicate Title"})

    # Try to create another with the same title
    response = client.post(
        "/conversations/",
        json={"conversation_title": "Duplicate Title"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Conversation already exists"


def test_get_conversation(client: TestClient):
    """Test GET /conversations/{id} returns the conversation with messages."""
    # Create a conversation first
    create_response = client.post(
        "/conversations/",
        json={"conversation_title": "Get Test Conversation"},
    )
    assert create_response.status_code == 200
    # ConversationCreate doesn't return id, so we have to use id=1 (first created)
    # A better approach would be for POST to return ConversationRead

    # Get the conversation - assuming first one has id=1
    response = client.get("/conversations/1")

    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == 1
    assert data["conversation_title"] == "Get Test Conversation"
    assert "created_at" in data
    assert "messages" in data
    assert data["messages"] == []


def test_get_conversation_not_found(client: TestClient):
    """Test GET /conversations/{id} returns 404 for non-existent conversation."""
    response = client.get("/conversations/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_delete_conversation(client: TestClient):
    """Test DELETE /conversations/{id} removes the conversation."""
    # Create a conversation first
    client.post(
        "/conversations/",
        json={"conversation_title": "Delete Test Conversation"},
    )
    # First created conversation has id=1

    # Delete the conversation
    response = client.delete("/conversations/1")

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get("/conversations/1")
    assert get_response.status_code == 404


def test_delete_conversation_not_found(client: TestClient):
    """Test DELETE /conversations/{id} returns 404 for non-existent conversation."""
    response = client.delete("/conversations/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"
