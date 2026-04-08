from datetime import datetime

from sqlmodel import Field, SQLModel


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(default=None, foreign_key="conversation.id")
    role: str = Field(index=False)
    content: str = Field(index=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
