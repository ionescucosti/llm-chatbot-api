from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ConversationMode(StrEnum):
    PLAIN = "plain"
    RAG = "rag"
    TOOLS = "tools"


class ConversationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    title: str = Field(alias="conversation_title")
    mode: ConversationMode = Field(default=ConversationMode.PLAIN)


class ConversationRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: int = Field(alias="conversation_id")
    title: str = Field(alias="conversation_title")
    mode: ConversationMode
    created_at: datetime


class MessageInHistory(BaseModel):
    role: str
    content: str


class ConversationWithHistory(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: int = Field(alias="conversation_id")
    title: str = Field(alias="conversation_title")
    mode: ConversationMode
    created_at: datetime
    messages: list[MessageInHistory] = []
