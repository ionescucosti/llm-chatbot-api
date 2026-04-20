import io
import logging

from docx import Document as DocxDocument
from openai import OpenAI
from pypdf import PdfReader

from core.config import settings
from core.text_splitter import RecursiveTextSplitter
from database.chroma import get_chroma_collection

logger = logging.getLogger(__name__)


class EmbeddingService:
    SUPPORTED_CONTENT_TYPES = {
        "application/pdf": "pdf",
        "text/plain": "txt",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    }

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.text_splitter = RecursiveTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
        )

    def extract_text(self, file_bytes: bytes, content_type: str) -> str:
        """Extract text from PDF, TXT, or DOCX files."""
        file_type = self.SUPPORTED_CONTENT_TYPES.get(content_type)

        if file_type == "pdf":
            return self._extract_from_pdf(file_bytes)
        elif file_type == "txt":
            return self._extract_from_txt(file_bytes)
        elif file_type == "docx":
            return self._extract_from_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

    def _extract_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF."""
        logger.info("Extracting text from PDF")
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def _extract_from_txt(self, file_bytes: bytes) -> str:
        """Extract text from TXT file."""
        logger.info("Extracting text from TXT")
        return file_bytes.decode("utf-8")

    def _extract_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX."""
        logger.info("Extracting text from DOCX")
        doc = DocxDocument(io.BytesIO(file_bytes))
        text_parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
        return "\n\n".join(text_parts)

    def chunk_text(self, text: str) -> list[str]:
        """Split text into chunks with overlap."""
        logger.info("Chunking text (length=%d)", len(text))
        chunks = self.text_splitter.split_text(text)
        logger.info("Created %d chunks", len(chunks))
        return chunks

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts using OpenAI."""
        logger.info("Generating embeddings for %d texts", len(texts))
        response = self.client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
        embeddings = [item.embedding for item in response.data]
        logger.info("Generated %d embeddings", len(embeddings))
        return embeddings

    def generate_single_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        return self.generate_embeddings([text])[0]

    def add_to_chroma(self, doc_id: int, filename: str, chunks: list[str], embeddings: list[list[float]]) -> int:
        """Add document chunks to ChromaDB collection."""
        logger.info("Adding %d chunks to ChromaDB for document %d", len(chunks), doc_id)
        collection = get_chroma_collection()

        ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"document_id": doc_id, "document_filename": filename, "chunk_index": i} for i in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        logger.info("Successfully added chunks to ChromaDB")
        return len(chunks)

    def search_chroma(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Search ChromaDB for similar chunks."""
        logger.info("Searching ChromaDB for top %d results", top_k)
        collection = get_chroma_collection()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0
                # Convert distance to similarity score (cosine distance to similarity)
                score = 1 - distance

                search_results.append(
                    {
                        "content": doc,
                        "score": score,
                        "document_id": metadata.get("document_id"),
                        "document_filename": metadata.get("document_filename", ""),
                        "chunk_index": metadata.get("chunk_index", 0),
                    }
                )

        logger.info("Found %d results", len(search_results))
        return search_results

    def delete_from_chroma(self, doc_id: int) -> None:
        """Delete all chunks for a document from ChromaDB."""
        logger.info("Deleting chunks for document %d from ChromaDB", doc_id)
        collection = get_chroma_collection()

        # Query to find all chunk IDs for this document
        collection.delete(where={"document_id": doc_id})
        logger.info("Deleted chunks for document %d", doc_id)
