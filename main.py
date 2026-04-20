import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from api.routes_conversations import router as conversation_router
from api.routes_documents import router as document_router
from api.routes_health import router as health_router
from api.routes_messages import router as message_router
from database.db import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created")
    yield
    logger.info("Shutting down application...")


app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s %s - %s", request.method, request.url.path, str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", tags=["Root"])
def read_root():
    return {"Hello": "World"}


app.include_router(health_router)
app.include_router(conversation_router)
app.include_router(message_router)
app.include_router(document_router)
