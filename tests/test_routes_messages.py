"""Tests for message endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_create_message(client: TestClient):
    """Test POST /conversations/{id}/messages creates a message and gets AI response."""
    # Create a conversation first
    client.post(
        "/conversations/",
        json={"conversation_title": "Message Test Conversation"},
    )
    # First conversation has id=1

    # Mock AIService to avoid real API calls
    with patch("services.message_service.AIService") as mock_ai_class:
        mock_ai_instance = mock_ai_class.return_value
        mock_ai_instance.generate_response.return_value = "This is a mocked AI response."

        response = client.post(
            "/conversations/1/messages",
            json={"content": "Hello, AI!"},
        )

    assert response.status_code == 200
    data = response.json()
    # Response uses MessageCreate schema which only has 'content'
    assert data["content"] == "This is a mocked AI response."


def test_create_message_conversation_not_found(client: TestClient):
    """Test POST /conversations/{id}/messages returns 400 for non-existent conversation."""
    with patch("services.message_service.AIService"):
        response = client.post(
            "/conversations/99999/messages",
            json={"content": "Hello!"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Conversation does not exist."


def test_get_message(client: TestClient):
    """Test GET /conversations/{c_id}/messages/{m_id} returns the message."""
    # Create a conversation
    client.post(
        "/conversations/",
        json={"conversation_title": "Get Message Test"},
    )

    # Create a message with mocked AI
    with patch("services.message_service.AIService") as mock_ai_class:
        mock_ai_instance = mock_ai_class.return_value
        mock_ai_instance.generate_response.return_value = "AI response"

        client.post(
            "/conversations/1/messages",
            json={"content": "Test message"},
        )
        # This creates user message (id=1) and assistant message (id=2)

    # Get the assistant message (id=2)
    response = client.get("/conversations/1/messages/2")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["conversation_id"] == 1


def test_get_message_conversation_not_found(client: TestClient):
    """Test GET /conversations/{c_id}/messages/{m_id} returns 404 for non-existent conversation."""
    response = client.get("/conversations/99999/messages/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"
