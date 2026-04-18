"""Unit tests for ConversationService."""

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from models.conversation import Conversation
from models.message import Message
from schemas.conversation import ConversationCreate
from services.conversation_service import ConversationService


class TestConversationService:
    """Test suite for ConversationService."""

    def test_create_conversation(self, session: Session):
        """Test creating a new conversation."""
        service = ConversationService(session)
        conversation_data = ConversationCreate(conversation_title="New Conversation")

        result = service.create_conversation(conversation_data)

        assert result.id is not None
        assert result.title == "New Conversation"
        assert result.created_at is not None

    def test_create_conversation_duplicate_title_raises_409(self, session: Session):
        """Test creating conversation with duplicate title raises HTTPException."""
        service = ConversationService(session)
        conversation_data = ConversationCreate(conversation_title="Duplicate")

        # Create first conversation
        service.create_conversation(conversation_data)

        # Try to create another with same title
        with pytest.raises(HTTPException) as exc_info:
            service.create_conversation(conversation_data)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "Conversation already exists"

    def test_get_conversation(self, session: Session):
        """Test getting an existing conversation with empty messages."""
        # Create a conversation directly
        conversation = Conversation(title="Test Get")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        service = ConversationService(session)
        result = service.get_conversation(conversation.id)  # type: ignore

        assert result.id == conversation.id
        assert result.title == "Test Get"
        assert result.messages == []

    def test_get_conversation_with_messages(self, session: Session):
        """Test getting a conversation includes chat history."""
        # Create a conversation
        conversation = Conversation(title="Test With Messages")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        # Add messages
        msg1 = Message(conversation_id=conversation.id, role="user", content="Hello")
        msg2 = Message(conversation_id=conversation.id, role="assistant", content="Hi there!")
        session.add_all([msg1, msg2])
        session.commit()

        service = ConversationService(session)
        result = service.get_conversation(conversation.id)  # type: ignore

        assert result.id == conversation.id
        assert len(result.messages) == 2
        assert result.messages[0].role == "user"
        assert result.messages[0].content == "Hello"
        assert result.messages[1].role == "assistant"
        assert result.messages[1].content == "Hi there!"

    def test_get_conversation_not_found_raises_404(self, session: Session):
        """Test getting non-existent conversation raises HTTPException."""
        service = ConversationService(session)

        with pytest.raises(HTTPException) as exc_info:
            service.get_conversation(99999)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Conversation not found"

    def test_delete_conversation(self, session: Session):
        """Test deleting an existing conversation."""
        # Create a conversation
        conversation = Conversation(title="Test Delete")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        conversation_id = conversation.id

        service = ConversationService(session)
        service.delete_conversation(conversation_id)  # type: ignore

        # Verify it's deleted
        deleted = session.get(Conversation, conversation_id)
        assert deleted is None

    def test_delete_conversation_not_found_raises_404(self, session: Session):
        """Test deleting non-existent conversation raises HTTPException."""
        service = ConversationService(session)

        with pytest.raises(HTTPException) as exc_info:
            service.delete_conversation(99999)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Conversation not found"
