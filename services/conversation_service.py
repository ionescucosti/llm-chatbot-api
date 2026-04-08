from fastapi import HTTPException
from sqlmodel import Session, select

from models.conversation import Conversation
from schemas.conversation import ConversationCreate


class ConversationService:
    def __init__(self, session: Session):
        self.session = session

    def create_conversation(self, conversation_data: ConversationCreate) -> Conversation:
        payload = conversation_data.model_dump(by_alias=False)
        statement = select(Conversation).where(Conversation.title == conversation_data.title)
        conversation = self.session.exec(statement).first()
        if conversation:
            raise HTTPException(status_code=409, detail="Conversation already exists")

        conversation = Conversation(**payload)
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: int) -> Conversation:
        conversation = self.session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation

    def delete_conversation(self, conversation_id: int) -> Conversation:
        conversation = self.session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        self.session.delete(conversation)
        self.session.commit()
