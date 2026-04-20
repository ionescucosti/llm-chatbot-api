from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class ConversationMode(StrEnum):
    PLAIN = "plain"
    RAG = "rag"
    TOOLS = "tools"


class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    mode: ConversationMode = Field(default=ConversationMode.PLAIN)
    created_at: datetime = Field(default_factory=utc_now)
