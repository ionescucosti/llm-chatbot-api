import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from database.db import get_session
from schemas.message import MessageCreate, MessageRead
from services.message_service import MessageService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Messages"])


@router.post("/conversations/{c_id}/messages", response_model=MessageCreate)
def create_message(c_id: int, message_data: MessageCreate, session: Annotated[Session, Depends(get_session)]):
    logger.info("POST /conversations/%s/messages - New message", c_id)
    service = MessageService(session)
    return service.create_message(c_id, message_data)


@router.get("/conversations/{c_id}/messages/{m_id}", response_model=MessageRead)
def get_message(c_id: int, m_id: int, session: Annotated[Session, Depends(get_session)]):
    logger.info("GET /conversations/%s/messages/%s", c_id, m_id)
    service = MessageService(session)
    return service.get_message(c_id, m_id)
