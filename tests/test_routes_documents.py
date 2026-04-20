"""Tests for document upload and search endpoints."""

from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from models.document import Document, DocumentStatus


class TestDocumentUpload:
    """Tests for POST /documents/upload endpoint."""

    def test_upload_document_success(self, client: TestClient, session: Session):
        """Test successful document upload returns 202 and queues processing."""
        file_content = b"This is a test document content for RAG processing."

        with patch("api.routes_documents.process_document_task") as mock_task:
            mock_task.delay = MagicMock()

            response = client.post(
                "/documents/upload",
                files={"file": ("test.txt", file_content, "text/plain")},
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["status"] == "pending"
        assert data["message"] == "Document queued for processing"
        assert "id" in data

        # Verify task was queued
        mock_task.delay.assert_called_once()

    def test_upload_document_unsupported_type(self, client: TestClient):
        """Test upload with unsupported file type returns 415."""
        response = client.post(
            "/documents/upload",
            files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
        )

        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        assert "Unsupported file type" in response.json()["detail"]

    def test_upload_document_too_large(self, client: TestClient):
        """Test upload with file exceeding max size returns 413."""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)

        response = client.post(
            "/documents/upload",
            files={"file": ("large.txt", large_content, "text/plain")},
        )

        assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
        assert "File too large" in response.json()["detail"]

    def test_upload_document_duplicate(self, client: TestClient, session: Session):
        """Test upload of duplicate file returns 409."""
        file_content = b"Duplicate document content"

        with patch("api.routes_documents.process_document_task") as mock_task:
            mock_task.delay = MagicMock()

            # First upload
            response1 = client.post(
                "/documents/upload",
                files={"file": ("test1.txt", file_content, "text/plain")},
            )
            assert response1.status_code == status.HTTP_202_ACCEPTED

            # Second upload with same content
            response2 = client.post(
                "/documents/upload",
                files={"file": ("test2.txt", file_content, "text/plain")},
            )

        assert response2.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response2.json()["detail"]

    def test_upload_pdf_document(self, client: TestClient, session: Session):
        """Test upload of PDF file."""
        # Minimal PDF content
        pdf_content = b"%PDF-1.4 test content"

        with patch("api.routes_documents.process_document_task") as mock_task:
            mock_task.delay = MagicMock()

            response = client.post(
                "/documents/upload",
                files={"file": ("document.pdf", pdf_content, "application/pdf")},
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json()["filename"] == "document.pdf"

    def test_upload_docx_document(self, client: TestClient, session: Session):
        """Test upload of DOCX file."""
        docx_content = b"PK\x03\x04 fake docx"

        with patch("api.routes_documents.process_document_task") as mock_task:
            mock_task.delay = MagicMock()

            response = client.post(
                "/documents/upload",
                files={
                    "file": (
                        "document.docx",
                        docx_content,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json()["filename"] == "document.docx"


class TestDocumentStatus:
    """Tests for GET /documents/{doc_id}/status endpoint."""

    def test_get_document_status(self, client: TestClient, session: Session):
        """Test getting status of an existing document."""
        # Create a document directly in the database
        document = Document(
            filename="test.txt",
            file_hash="abc123",
            status=DocumentStatus.COMPLETED,
            chunk_count=5,
        )
        session.add(document)
        session.commit()
        session.refresh(document)

        response = client.get(f"/documents/{document.id}/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == document.id
        assert data["filename"] == "test.txt"
        assert data["status"] == "completed"
        assert data["chunk_count"] == 5

    def test_get_document_status_not_found(self, client: TestClient):
        """Test getting status of non-existent document returns 404."""
        response = client.get("/documents/99999/status")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_get_document_status_with_error(self, client: TestClient, session: Session):
        """Test getting status of failed document includes error message."""
        document = Document(
            filename="failed.pdf",
            file_hash="failed123",
            status=DocumentStatus.FAILED,
            error_message="Could not extract text from PDF",
        )
        session.add(document)
        session.commit()
        session.refresh(document)

        response = client.get(f"/documents/{document.id}/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Could not extract text from PDF"


class TestDocumentList:
    """Tests for GET /documents endpoint."""

    def test_list_documents_empty(self, client: TestClient):
        """Test listing documents when none exist."""
        response = client.get("/documents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0

    def test_list_documents(self, client: TestClient, session: Session):
        """Test listing multiple documents."""
        doc1 = Document(filename="doc1.txt", file_hash="hash1", status=DocumentStatus.COMPLETED)
        doc2 = Document(filename="doc2.pdf", file_hash="hash2", status=DocumentStatus.PROCESSING)
        session.add(doc1)
        session.add(doc2)
        session.commit()

        response = client.get("/documents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert len(data["documents"]) == 2


class TestDocumentDelete:
    """Tests for DELETE /documents/{doc_id} endpoint."""

    def test_delete_document(self, client: TestClient, session: Session):
        """Test deleting an existing document."""
        document = Document(filename="to_delete.txt", file_hash="delete123", status=DocumentStatus.COMPLETED)
        session.add(document)
        session.commit()
        session.refresh(document)

        with patch("api.routes_documents.EmbeddingService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance

            response = client.delete(f"/documents/{document.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify document is deleted
        assert session.get(Document, document.id) is None

    def test_delete_document_not_found(self, client: TestClient):
        """Test deleting non-existent document returns 404."""
        response = client.delete("/documents/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDocumentSearch:
    """Tests for POST /documents/search endpoint."""

    def test_search_documents(self, client: TestClient):
        """Test searching documents."""
        with patch("api.routes_documents.EmbeddingService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            mock_instance.generate_single_embedding.return_value = [0.1] * 1536
            mock_instance.search_chroma.return_value = [
                {
                    "content": "This is a relevant chunk",
                    "score": 0.95,
                    "document_id": 1,
                    "document_filename": "test.txt",
                    "chunk_index": 0,
                }
            ]

            response = client.post("/documents/search", json={"query": "test query", "top_k": 5})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "test query"
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["content"] == "This is a relevant chunk"
        assert data["results"][0]["score"] == 0.95

    def test_search_documents_empty_query(self, client: TestClient):
        """Test search with empty query returns validation error."""
        response = client.post("/documents/search", json={"query": "", "top_k": 5})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_search_documents_invalid_top_k(self, client: TestClient):
        """Test search with invalid top_k returns validation error."""
        response = client.post("/documents/search", json={"query": "test", "top_k": 100})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
