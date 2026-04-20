"""Unit tests for MessageService."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlmodel import Session, select

from models.conversation import Conversation, ConversationMode
from models.message import Message
from schemas.message import MessageCreate
from services.message_service import MessageService


class TestMessageService:
    """Test suite for MessageService."""

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_create_message(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test creating a message with AI response."""
        # Setup mock
        mock_ai_instance = mock_ai_class.return_value
        mock_ai_instance.generate_response.return_value = "AI says hello!"

        # Create a conversation first
        conversation = Conversation(title="Test Conversation")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        service = MessageService(session)
        message_data = MessageCreate(content="Hello AI")

        result = service.create_message(conversation.id, message_data)

        # Should return the assistant message
        assert result.role == "assistant"
        assert result.content == "AI says hello!"
        assert result.conversation_id == conversation.id
        mock_ai_instance.generate_response.assert_called_once()

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_create_message_rag_mode(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test creating a message with RAG mode."""
        # Setup mock
        mock_rag_instance = mock_rag_class.return_value
        mock_rag_instance.generate_response.return_value = "RAG response!"

        # Create a conversation with RAG mode
        conversation = Conversation(title="RAG Conversation", conversation_mode=ConversationMode.RAG)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        service = MessageService(session)
        message_data = MessageCreate(content="Search something")

        result = service.create_message(conversation.id, message_data)

        assert result.role == "assistant"
        assert result.content == "RAG response!"
        mock_rag_instance.generate_response.assert_called_once()

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_create_message_tools_mode(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test creating a message with tools mode."""
        # Setup mock
        mock_tools_instance = mock_tools_class.return_value
        mock_tools_instance.generate_response.return_value = "Tools response!"

        # Create a conversation with tools mode
        conversation = Conversation(title="Tools Conversation", conversation_mode=ConversationMode.TOOLS)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        service = MessageService(session)
        message_data = MessageCreate(content="What time is it?")

        result = service.create_message(conversation.id, message_data)

        assert result.role == "assistant"
        assert result.content == "Tools response!"
        mock_tools_instance.generate_response.assert_called_once()

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_create_message_saves_user_message(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test that user message is also saved to database."""
        mock_ai_instance = mock_ai_class.return_value
        mock_ai_instance.generate_response.return_value = "AI response"

        conversation = Conversation(title="Test Conversation")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        service = MessageService(session)
        message_data = MessageCreate(content="User message")
        service.create_message(conversation.id, message_data)

        # Check that both user and assistant messages were saved
        statement = select(Message).where(Message.conversation_id == conversation.id)
        messages = session.exec(statement).all()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "User message"
        assert messages[1].role == "assistant"

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_create_message_conversation_not_found(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test creating message for non-existent conversation raises HTTPException."""
        service = MessageService(session)
        message_data = MessageCreate(content="Hello")

        with pytest.raises(HTTPException) as exc_info:
            service.create_message(99999, message_data)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Conversation does not exist."

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_get_message(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test getting an existing message."""
        # Create conversation and message
        conversation = Conversation(title="Test")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        message = Message(conversation_id=conversation.id, role="user", content="Test message")
        session.add(message)
        session.commit()
        session.refresh(message)

        service = MessageService(session)
        result = service.get_message(conversation.id, message.id)

        assert result.id == message.id
        assert result.content == "Test message"
        assert result.role == "user"

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_get_message_conversation_not_found(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test getting message from non-existent conversation raises HTTPException."""
        service = MessageService(session)

        with pytest.raises(HTTPException) as exc_info:
            service.get_message(99999, 1)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Conversation not found"

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_get_chat_history(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test getting chat history for a conversation."""
        # Create conversation
        conversation = Conversation(title="Chat History Test")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        # Create messages
        msg1 = Message(conversation_id=conversation.id, role="user", content="Hello")
        msg2 = Message(conversation_id=conversation.id, role="assistant", content="Hi there!")
        msg3 = Message(conversation_id=conversation.id, role="user", content="How are you?")
        session.add_all([msg1, msg2, msg3])
        session.commit()

        service = MessageService(session)
        history = service.get_chat_history(conversation.id)

        assert len(history) == 3
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi there!"}
        assert history[2] == {"role": "user", "content": "How are you?"}

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_get_chat_history_conversation_not_found(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test getting chat history for non-existent conversation raises HTTPException."""
        service = MessageService(session)

        with pytest.raises(HTTPException) as exc_info:
            service.get_chat_history(99999)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Conversation not found"

    @patch("services.message_service.ToolsService")
    @patch("services.message_service.RAGService")
    @patch("services.message_service.AIService")
    def test_get_chat_history_empty(
        self, mock_ai_class: MagicMock, mock_rag_class: MagicMock, mock_tools_class: MagicMock, session: Session
    ):
        """Test getting chat history for conversation with no messages."""
        conversation = Conversation(title="Empty Conversation")
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        service = MessageService(session)
        history = service.get_chat_history(conversation.id)

        assert history == []
