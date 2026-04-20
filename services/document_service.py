import hashlib
import logging
from datetime import UTC, datetime

from sqlalchemy import desc
from sqlmodel import Session, select

from models.document import Document, DocumentStatus

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def compute_file_hash(file_bytes: bytes) -> str:
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(file_bytes).hexdigest()

    def get_by_hash(self, file_hash: str) -> Document | None:
        """Get document by file hash to check for duplicates."""
        statement = select(Document).where(Document.file_hash == file_hash)
        return self.session.exec(statement).first()

    def create_pending(self, filename: str, file_hash: str) -> Document:
        """Create a new document record with pending status."""
        logger.info("Creating pending document: %s", filename)
        document = Document(
            filename=filename,
            file_hash=file_hash,
            status=DocumentStatus.PENDING,
        )
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        logger.info("Created document id=%d", document.id)
        return document

    def get_document(self, doc_id: int) -> Document | None:
        """Get document by ID."""
        return self.session.get(Document, doc_id)

    def list_documents(self) -> list[Document]:
        """List all documents."""
        statement = select(Document).order_by(desc(Document.created_at))
        return list(self.session.exec(statement).all())

    def update_status(
        self,
        doc_id: int,
        status: DocumentStatus,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> Document | None:
        """Update document status."""
        document = self.session.get(Document, doc_id)
        if not document:
            logger.warning("Document %d not found for status update", doc_id)
            return None

        document.status = status
        if chunk_count is not None:
            document.chunk_count = chunk_count
        if error_message is not None:
            document.error_message = error_message
        if status in (DocumentStatus.COMPLETED, DocumentStatus.FAILED):
            document.completed_at = datetime.now(UTC)

        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        logger.info("Updated document %d status to %s", doc_id, status)
        return document

    def delete_document(self, doc_id: int) -> bool:
        """Delete a document."""
        document = self.session.get(Document, doc_id)
        if not document:
            return False

        self.session.delete(document)
        self.session.commit()
        logger.info("Deleted document %d", doc_id)
        return True
