import logging

from fastapi import HTTPException
from sqlmodel import Session, select

from models.conversation import Conversation
from models.message import Message
from schemas.conversation import ConversationCreate, ConversationWithHistory

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, session: Session):
        self.session = session

    def create_conversation(self, conversation_data: ConversationCreate) -> Conversation:
        payload = conversation_data.model_dump(by_alias=False)
        statement = select(Conversation).where(Conversation.title == conversation_data.title)
        conversation = self.session.exec(statement).first()
        if conversation:
            logger.warning("Conversation already exists: %s", conversation_data.title)
            raise HTTPException(status_code=409, detail="Conversation already exists")

        conversation = Conversation(**payload)
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        logger.info("Created conversation id=%s title=%s", conversation.id, conversation.title)
        return conversation

    def get_conversation(self, conversation_id: int) -> ConversationWithHistory:
        conversation = self.session.get(Conversation, conversation_id)
        if not conversation:
            logger.warning("Conversation not found: id=%s", conversation_id)
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get chat history
        statement = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
        messages = self.session.exec(statement).all()
        chat_history = [{"role": m.role, "content": m.content} for m in messages]

        return ConversationWithHistory(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            messages=chat_history,
        )

    def delete_conversation(self, conversation_id: int) -> Conversation:
        conversation = self.session.get(Conversation, conversation_id)
        if not conversation:
            logger.warning("Conversation not found for deletion: id=%s", conversation_id)
            raise HTTPException(status_code=404, detail="Conversation not found")
        self.session.delete(conversation)
        self.session.commit()
        logger.info("Deleted conversation id=%s", conversation_id)
