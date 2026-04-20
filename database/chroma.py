import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

from core.config import settings

logger = logging.getLogger(__name__)

# Singleton ChromaDB client with persistence
_chroma_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create the ChromaDB persistent client singleton."""
    global _chroma_client
    if _chroma_client is None:
        logger.info("Initializing ChromaDB client at %s", settings.chroma_persist_dir)
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB client initialized")
    return _chroma_client


def get_chroma_collection(name: str | None = None) -> chromadb.Collection:
    """Get or create a ChromaDB collection."""
    collection_name = name or settings.chroma_collection_name
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
