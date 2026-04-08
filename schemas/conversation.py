from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    title: str = Field(alias="conversation_title")


class ConversationRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: int = Field(alias="conversation_id")
    title: str = Field(alias="conversation_title")
    created_at: datetime
