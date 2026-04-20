from datetime import datetime

from pydantic import BaseModel, Field

from models.document import DocumentStatus


# Upload Response
class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    status: DocumentStatus
    message: str = "Document queued for processing"


# Status Response
class DocumentStatusResponse(BaseModel):
    id: int
    filename: str
    status: DocumentStatus
    chunk_count: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


# List Response
class DocumentListResponse(BaseModel):
    documents: list[DocumentStatusResponse]
    total: int


# Search Request/Response
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    content: str
    score: float
    document_id: int
    document_filename: str
    chunk_index: int


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
