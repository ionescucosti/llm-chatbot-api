from datetime import datetime

from sqlmodel import Field, SQLModel


class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
