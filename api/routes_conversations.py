import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from database.db import get_session
from schemas.conversation import ConversationCreate, ConversationWithHistory
from services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("/", response_model=ConversationCreate)
def create_conversation(conversation_data: ConversationCreate, session: Annotated[Session, Depends(get_session)]):
    logger.info("POST /conversations - Creating conversation: %s", conversation_data.title)
    service = ConversationService(session)
    return service.create_conversation(conversation_data)


@router.get("/{conversation_id}", response_model=ConversationWithHistory)
def read_conversation(conversation_id: int, session: Annotated[Session, Depends(get_session)]):
    logger.info("GET /conversations/%s", conversation_id)
    service = ConversationService(session)
    return service.get_conversation(conversation_id)


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, session: Annotated[Session, Depends(get_session)]):
    logger.info("DELETE /conversations/%s", conversation_id)
    service = ConversationService(session)
    service.delete_conversation(conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
