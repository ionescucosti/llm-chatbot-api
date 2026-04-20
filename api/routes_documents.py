import base64
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session

from core.config import settings
from database.db import get_session
from schemas.document import (
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from services.document_service import DocumentService
from services.embedding_service import EmbeddingService
from workers.tasks import process_document_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF, TXT, or DOCX file to upload")],
    session: Annotated[Session, Depends(get_session)],
):
    """
    Upload a document for RAG processing.

    The document will be processed asynchronously:
    1. Text extraction
    2. Chunking
    3. Embedding generation
    4. Storage in vector database

    Returns 202 Accepted with document ID. Use GET /documents/{doc_id}/status to check progress.
    """
    logger.info("POST /documents/upload - filename=%s, content_type=%s", file.filename, file.content_type)

    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, TXT, DOCX",
        )

    # Read file content
    file_bytes = await file.read()

    # Validate file size
    max_size = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
        )

    # Check for duplicate
    service = DocumentService(session)
    file_hash = service.compute_file_hash(file_bytes)
    existing = service.get_by_hash(file_hash)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document already exists with id={existing.id}",
        )

    # Create pending document record
    filename = file.filename or "unnamed_file"
    document = service.create_pending(filename, file_hash)

    # Enqueue Celery task (encode bytes as base64 for JSON serialization)
    file_bytes_b64 = base64.b64encode(file_bytes).decode("utf-8")
    process_document_task.delay(document.id, file_bytes_b64, file.content_type, filename)
    logger.info("Enqueued processing task for document %d", document.id)

    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        message="Document queued for processing",
    )


@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    doc_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    """Get the processing status of a document."""
    logger.info("GET /documents/%d/status", doc_id)
    service = DocumentService(session)
    document = service.get_document(doc_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found",
        )

    return DocumentStatusResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at,
        completed_at=document.completed_at,
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(session: Annotated[Session, Depends(get_session)]):
    """List all uploaded documents."""
    logger.info("GET /documents")
    service = DocumentService(session)
    documents = service.list_documents()

    return DocumentListResponse(
        documents=[
            DocumentStatusResponse(
                id=doc.id,
                filename=doc.filename,
                status=doc.status,
                chunk_count=doc.chunk_count,
                error_message=doc.error_message,
                created_at=doc.created_at,
                completed_at=doc.completed_at,
            )
            for doc in documents
        ],
        total=len(documents),
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    """Delete a document and its chunks from the vector database."""
    logger.info("DELETE /documents/%d", doc_id)
    service = DocumentService(session)
    document = service.get_document(doc_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found",
        )

    # Delete from ChromaDB first
    embedding_service = EmbeddingService()
    embedding_service.delete_from_chroma(doc_id)

    # Delete from database
    service.delete_document(doc_id)
    logger.info("Document %d deleted successfully", doc_id)


@router.post("/search", response_model=SearchResponse)
def search_documents(
    search_request: SearchRequest,
):
    """
    Search for similar content in uploaded documents.

    Uses semantic similarity to find the most relevant document chunks.
    """
    logger.info("POST /documents/search - query=%s, top_k=%d", search_request.query[:50], search_request.top_k)

    embedding_service = EmbeddingService()

    # Generate embedding for the query
    query_embedding = embedding_service.generate_single_embedding(search_request.query)

    # Search ChromaDB
    results = embedding_service.search_chroma(query_embedding, search_request.top_k)

    return SearchResponse(
        query=search_request.query,
        results=[
            SearchResult(
                content=r["content"],
                score=r["score"],
                document_id=r["document_id"],
                document_filename=r["document_filename"],
                chunk_index=r["chunk_index"],
            )
            for r in results
        ],
        total=len(results),
    )
