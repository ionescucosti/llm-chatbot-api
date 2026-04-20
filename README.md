# llm-chatbot-api

`llm-chatbot-api` is a FastAPI backend for managing chat conversations with AI-powered responses and RAG (Retrieval-Augmented Generation) capabilities. It stores conversation history in PostgreSQL, integrates with OpenAI for AI responses and embeddings, and uses ChromaDB for vector storage.

## What It Does

- Creates and deletes conversations
- Stores user and assistant messages per conversation
- **RAG Document Ingestion**: Upload PDF, TXT, DOCX files for knowledge base
- **Async Processing**: Background document processing with Celery
- **Semantic Search**: Query uploaded documents using vector similarity
- Exposes REST endpoints for health checks, conversations, messages, and documents
- Persists data in PostgreSQL and ChromaDB

## Tech Stack

- Python 3.14
- FastAPI
- SQLModel + SQLAlchemy
- PostgreSQL + Psycopg
- **ChromaDB** (vector database)
- **Celery + Redis** (async task queue)
- **OpenAI Embeddings** (text-embedding-3-small)
- **PyPDF + python-docx** (document parsing)
- Docker & Docker Compose
- GitHub Actions for CI
- `uv` for dependency management
- Ruff for formatting and linting
- Pre-commit for local commit-time checks

## Project Structure

```text
.
├── .github/workflows/  # CI/CD workflows
├── api/                # FastAPI route handlers
│   ├── routes_conversations.py
│   ├── routes_documents.py    # NEW: Document upload & search
│   ├── routes_health.py
│   └── routes_messages.py
├── core/               # Configuration and utilities
│   ├── celery_app.py          # NEW: Celery configuration
│   ├── config.py
│   ├── prompts.py
│   └── text_splitter.py       # NEW: Custom text chunking
├── database/           # Database connections
│   ├── chroma.py              # NEW: ChromaDB client
│   └── db.py                  # PostgreSQL engine
├── models/             # SQLModel table definitions
│   ├── conversation.py
│   ├── document.py            # NEW: Document model
│   └── message.py
├── schemas/            # Request and response schemas
│   ├── conversation.py
│   ├── document.py            # NEW: Document schemas
│   └── message.py
├── services/           # Business logic
│   ├── ai_service.py
│   ├── conversation_service.py
│   ├── document_service.py    # NEW: Document CRUD
│   ├── embedding_service.py   # NEW: Text extraction & embeddings
│   └── message_service.py
├── workers/            # NEW: Background tasks
│   └── tasks.py               # Celery tasks
├── tests/              # Unit and endpoint tests
├── main.py             # FastAPI application entrypoint
├── Dockerfile
├── compose.yaml
├── pyproject.toml
└── uv.lock
```

## Getting Started

### With Docker Compose (Recommended)

1. Copy the environment file and set your OpenAI API key:

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

2. Start all services:

```bash
docker compose up -d
```

This starts:
- **PostgreSQL** database on port 5432
- **Redis** for Celery task queue on port 6379
- **API server** on port 8000
- **Celery worker** for async document processing

The API will be available at `http://localhost:8000`.

### Local Development

Install dependencies:

```bash
uv sync
```

Install dev dependencies as well:

```bash
uv sync --dev
```

Start PostgreSQL and Redis (via Docker):

```bash
docker compose up -d db redis
```

Run the development server:

```bash
uv run fastapi dev main.py
```

Start the Celery worker (in a separate terminal):

```bash
uv run celery -A core.celery_app worker --loglevel=info
```

The API will be available at `http://127.0.0.1:8000`.

## Development Tooling

The project includes a small local quality gate for Python code:

- `ruff format` for code formatting
- `ruff check --fix` for linting and auto-fixes
- `pylint` as an additional dev dependency for manual static analysis
- `pre-commit` to run the Ruff hooks before commits

Useful commands:

```bash
uv run ruff format .
uv run ruff check . --fix
uv run pylint .
```

Set up git hooks:

```bash
uv run pre-commit install
```

Run all pre-commit hooks manually:

```bash
uv run pre-commit run --all-files
```

## Testing

The project includes unit tests and endpoint tests using pytest.

Run all tests:

```bash
uv run pytest
```

Run tests with verbose output:

```bash
uv run pytest -v
```

### Test Structure

```text
tests/
├── conftest.py                    # Fixtures with in-memory SQLite database
├── test_routes_health.py          # Health endpoint tests
├── test_routes_conversations.py   # Conversation endpoint tests
├── test_routes_messages.py        # Message endpoint tests
├── test_routes_documents.py       # Document upload & search tests
├── test_conversation_service.py   # ConversationService unit tests
└── test_message_service.py        # MessageService unit tests
```

### Test Database

Tests use an isolated SQLite in-memory database. The test session is injected via FastAPI's `dependency_overrides` mechanism, so the development database (`chatbot`) is never touched during testing.

## CI/CD

The project uses GitHub Actions for continuous integration. On every push or pull request to `main`:

1. **Test & Lint** - Runs linter, format check, and all tests
2. **Build & Smoke Test** - Builds Docker image and runs health checks

The workflow is defined in `.github/workflows/ci.yml`.

## Docker

Build the Docker image:

```bash
docker build -t llm-chatbot-api .
```

Run the container:

```bash
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=your-api-key \
  -e DATABASE_URL=postgresql+psycopg://user:password@localhost/dbname \
  -e DEFAULT_LANGUAGE=en \
  --name chatbot-api \
  llm-chatbot-api
```

The API will be available at `http://localhost:8000`.

To persist the database, mount a volume:

```bash
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=your-api-key \
  -e DATABASE_URL=postgresql+psycopg://user:password@localhost/dbname \
  -e DEFAULT_LANGUAGE=en \
  -v $(pwd)/data:/app/data \
  --name chatbot-api \
  llm-chatbot-api
```

## API Overview

### Root

- `GET /`
  Returns a simple welcome payload.

### Health

- `GET /health`
  Returns the service health status.

### Conversations

- `POST /conversations/`
  Creates a new conversation.

Request body:

```json
{
  "conversation_title": "Support chat"
}
```

- `GET /conversations/{conversation_id}`
  Fetches a conversation by id.

- `DELETE /conversations/{conversation_id}`
  Deletes a conversation by id.

### Messages

- `POST /conversations/{c_id}/messages`
  Stores a user message, generates an assistant reply, and returns the assistant message.

Request body:

```json
{
  "content": "Hello"
}
```

- `GET /conversations/{c_id}/messages/{m_id}`
  Fetches a message by id for a given conversation.

### Documents (RAG)

#### Upload Document

- `POST /documents/upload`
  Upload a document for RAG processing. Supports PDF, TXT, and DOCX files up to 10MB.

Request: `multipart/form-data` with `file` field.

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf"
```

Response (202 Accepted):

```json
{
  "id": 1,
  "filename": "document.pdf",
  "status": "pending",
  "message": "Document queued for processing"
}
```

#### Get Document Status

- `GET /documents/{doc_id}/status`
  Check the processing status of a document.

Response:

```json
{
  "id": 1,
  "filename": "document.pdf",
  "status": "completed",
  "chunk_count": 42,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:31:15Z"
}
```

**Status values:**
- `pending` - Document queued for processing
- `processing` - Text extraction and embedding in progress
- `completed` - Document successfully processed
- `failed` - Processing failed (see `error_message`)

#### List Documents

- `GET /documents`
  List all uploaded documents.

Response:

```json
{
  "documents": [
    {
      "id": 1,
      "filename": "document.pdf",
      "status": "completed",
      "chunk_count": 42,
      "error_message": null,
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:31:15Z"
    }
  ],
  "total": 1
}
```

#### Delete Document

- `DELETE /documents/{doc_id}`
  Delete a document and its chunks from the vector database.

Response: `204 No Content`

#### Search Documents

- `POST /documents/search`
  Semantic search across all uploaded documents.

Request body:

```json
{
  "query": "How do I configure the application?",
  "top_k": 5
}
```

Response:

```json
{
  "query": "How do I configure the application?",
  "results": [
    {
      "content": "To configure the application, edit the .env file...",
      "score": 0.92,
      "document_id": 1,
      "document_filename": "setup-guide.pdf",
      "chunk_index": 3
    }
  ],
  "total": 1
}
```

## RAG Document Processing Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  POST /upload   │────▶│  Create Record  │────▶│  Queue Celery   │
│  (API)          │     │  status=pending │     │  Task           │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌────────────────────────────────┘
                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Celery Worker  │────▶│  Extract Text   │────▶│  Chunk Text     │
│  Picks Up Task  │     │  (PDF/TXT/DOCX) │     │  (1000 chars)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌────────────────────────────────┘
                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Generate       │────▶│  Store in       │────▶│  Update Status  │
│  Embeddings     │     │  ChromaDB       │     │  status=complete│
│  (OpenAI)       │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Processing Details

- **Text Extraction**: PyPDF for PDFs, python-docx for DOCX, UTF-8 decode for TXT
- **Chunking**: Custom `RecursiveTextSplitter` with 1000 character chunks and 200 character overlap
- **Embeddings**: OpenAI `text-embedding-3-small` model (1536 dimensions)
- **Vector Storage**: ChromaDB with cosine similarity
- **Deduplication**: SHA-256 file hash prevents duplicate uploads

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DATABASE_URL` | PostgreSQL connection URL (required) | - |
| `REDIS_URL` | Redis connection URL for Celery | `redis://localhost:6379/0` |
| `CHROMA_PERSIST_DIR` | ChromaDB persistence directory | `./chroma_data` |
| `CHROMA_COLLECTION_NAME` | ChromaDB collection name | `documents` |
| `EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-3-small` |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | `10` |
| `OPENAI_MODEL` | OpenAI chat model | `gpt-4.1-mini` |
| `ASSISTANT_MODE` | Assistant personality mode | `general` |
| `DEFAULT_LANGUAGE` | Default response language | `en` |

### Example `.env` file

```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot
REDIS_URL=redis://localhost:6379/0
CHROMA_PERSIST_DIR=./chroma_data
MAX_FILE_SIZE_MB=10
```

## Current Behavior

- Tables are created automatically on application startup.
- The AI integration uses OpenAI's API for chat completions.
- Conversation titles must be unique.
- Message creation stores both the user message and the generated assistant reply.
- **Document uploads are processed asynchronously** via Celery workers.
- **Duplicate documents** (same content hash) are rejected with 409 Conflict.
- **Supported file types**: PDF, TXT, DOCX (max 10MB by default).
- **ChromaDB** persists vector data to disk for durability.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Client                                │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Application                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Conversations│  │  Messages   │  │     Documents       │   │
│  │   Router    │  │   Router    │  │      Router         │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │
│         │                │                     │              │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────────┴──────────┐   │
│  │ Conversation│  │   Message   │  │    Document         │   │
│  │  Service    │  │   Service   │  │    Service          │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │
└─────────┼────────────────┼────────────────────┼──────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌─────────────────┐  ┌─────────────┐  ┌─────────────────────┐
│   PostgreSQL    │  │   OpenAI    │  │   Celery + Redis    │
│   (SQLModel)    │  │    API      │  │   (Async Tasks)     │
└─────────────────┘  └─────────────┘  └──────────┬──────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │  Embedding Service  │
                                      │  ┌───────────────┐  │
                                      │  │ Text Extract  │  │
                                      │  │ Chunking      │  │
                                      │  │ Embeddings    │  │
                                      │  └───────┬───────┘  │
                                      └──────────┼──────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │     ChromaDB        │
                                      │  (Vector Storage)   │
                                      └─────────────────────┘
```

## Notes

- Data is stored in a PostgreSQL database.
- Vector embeddings are stored in ChromaDB with persistence.
- Interactive API docs are available at `/docs` when the server is running.
- Ruff configuration lives in `pyproject.toml`.
- Pre-commit hooks are defined in `.pre-commit-config.yaml`.
- Celery tasks are defined in `workers/tasks.py`.
- Document processing happens asynchronously - poll `/documents/{id}/status` for progress.

## License

MIT
