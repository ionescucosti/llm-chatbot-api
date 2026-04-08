from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

from api.routes_conversations import router as conversation_router
from api.routes_health import router as health_router
from api.routes_messages import router as message_router
from database.db import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/", tags=["Root"])
def read_root():
    return {"Hello": "World"}


app.include_router(health_router)
app.include_router(conversation_router)
app.include_router(message_router)
