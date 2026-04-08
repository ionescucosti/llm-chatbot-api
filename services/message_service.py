from fastapi import HTTPException
from sqlmodel import Session, select

from models.conversation import Conversation
from models.message import Message
from services.ai_service import AIService


class MessageService:
    def __init__(self, session: Session):
        self.session = session
        self.ai_service = AIService()

    def create_message(self, conversation_id, message_data):
        payload = message_data.model_dump(by_alias=False)
        statement = select(Conversation).where(Conversation.id == conversation_id)
        conversation = self.session.exec(statement).first()
        if not conversation:
            raise HTTPException(status_code=400, detail="Conversation does not exist.")

        message = Message(conversation_id=conversation_id, role="user", content=payload["content"])
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)

        ai_response_text = self.ai_service.generate_response(payload["content"])
        assistant_message = Message(conversation_id=conversation_id, role="assistant", content=ai_response_text)
        self.session.add(assistant_message)
        self.session.commit()
        self.session.refresh(assistant_message)

        return assistant_message

    def get_message(self, conversation_id, message_id):
        conversation = self.session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        message = self.session.get(Message, message_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Message not found")

        return message
