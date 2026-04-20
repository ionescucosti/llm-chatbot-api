import base64
import logging

from sqlmodel import Session

from core.celery_app import celery_app
from database.db import engine
from models.document import DocumentStatus
from services.document_service import DocumentService
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self, doc_id: int, file_bytes_b64: str, content_type: str, filename: str):
    """
    Process a document: extract text, chunk, generate embeddings, store in ChromaDB.

    Args:
        doc_id: Document ID in the database
        file_bytes_b64: Base64 encoded file content
        content_type: MIME type of the file
        filename: Original filename
    """
    logger.info("Starting document processing task for doc_id=%d", doc_id)

    # Decode file bytes from base64
    file_bytes = base64.b64decode(file_bytes_b64)

    with Session(engine) as session:
        document_service = DocumentService(session)
        embedding_service = EmbeddingService()

        try:
            # Update status to processing
            document_service.update_status(doc_id, DocumentStatus.PROCESSING)

            # Step 1: Extract text
            logger.info("Extracting text from document %d", doc_id)
            text = embedding_service.extract_text(file_bytes, content_type)

            if not text.strip():
                raise ValueError("No text content could be extracted from the file")

            # Step 2: Chunk text
            logger.info("Chunking text for document %d", doc_id)
            chunks = embedding_service.chunk_text(text)

            if not chunks:
                raise ValueError("No chunks created from text content")

            # Step 3: Generate embeddings
            logger.info("Generating embeddings for document %d (%d chunks)", doc_id, len(chunks))
            embeddings = embedding_service.generate_embeddings(chunks)

            # Step 4: Store in ChromaDB
            logger.info("Storing chunks in ChromaDB for document %d", doc_id)
            chunk_count = embedding_service.add_to_chroma(doc_id, filename, chunks, embeddings)

            # Update status to completed
            document_service.update_status(
                doc_id,
                DocumentStatus.COMPLETED,
                chunk_count=chunk_count,
            )
            logger.info("Document %d processing completed successfully", doc_id)

        except Exception as e:
            logger.error("Document %d processing failed: %s", doc_id, str(e))
            document_service.update_status(
                doc_id,
                DocumentStatus.FAILED,
                error_message=str(e),
            )
            # Re-raise for Celery retry mechanism (optional)
            # raise self.retry(exc=e)
