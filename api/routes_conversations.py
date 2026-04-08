from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from database.db import get_session
from schemas.conversation import ConversationCreate, ConversationRead
from services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("/", response_model=ConversationCreate)
def create_conversation(conversation_data: ConversationCreate, session: Annotated[Session, Depends(get_session)]):
    service = ConversationService(session)
    return service.create_conversation(conversation_data)


@router.get("/{conversation_id}", response_model=ConversationRead)
def read_conversation(conversation_id: int, session: Annotated[Session, Depends(get_session)]):
    service = ConversationService(session)
    return service.get_conversation(conversation_id)


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, session: Annotated[Session, Depends(get_session)]):
    service = ConversationService(session)
    service.delete_conversation(conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
