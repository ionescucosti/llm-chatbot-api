# llm-chatbot-api

`llm-chatbot-api` is a small FastAPI backend for managing chat conversations and messages. It stores conversation history in PostgreSQL through SQLModel and integrates with OpenAI for AI-powered responses.

## What It Does

- Creates and deletes conversations
- Stores user and assistant messages per conversation
- Exposes simple REST endpoints for health checks, conversations, and messages
- Persists data in PostgreSQL

## Tech Stack

- Python 3.14
- FastAPI
- SQLModel + SQLAlchemy
- PostgreSQL + Psycopg
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
├── database/           # Database engine and session wiring
├── models/             # SQLModel table definitions
├── schemas/            # Request and response schemas
├── services/           # Business logic and AI integration
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

2. Start the services:

```bash
docker compose up -d
```

This starts:
- PostgreSQL database on port 5432
- API server on port 8000

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

Start PostgreSQL (via Docker):

```bash
docker compose up -d db
```

Run the development server:

```bash
uv run fastapi dev main.py
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

## Current Behavior

- Tables are created automatically on application startup.
- The AI integration is currently a stub in `services/ai_service.py`.
- Conversation titles must be unique.
- Message creation stores both the user message and the generated assistant reply.

## Notes

- Data is stored in a PostgreSQL database.
- Interactive API docs are available at `/docs` when the server is running.
- Ruff configuration lives in `pyproject.toml`.
- Pre-commit hooks are defined in `.pre-commit-config.yaml`.
