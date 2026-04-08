# llm-chatbot-api

`llm-chatbot-api` is a small FastAPI backend for managing chat conversations and messages. It stores conversation history in SQLite through SQLModel and currently uses a placeholder AI service that returns a generated string for each user message.

## What It Does

- Creates and deletes conversations
- Stores user and assistant messages per conversation
- Exposes simple REST endpoints for health checks, conversations, and messages
- Persists data locally in `database.db`

## Tech Stack

- Python 3.14
- FastAPI
- SQLModel
- SQLite
- `uv` for dependency management
- Ruff for formatting and linting
- Pre-commit for local commit-time checks

## Project Structure

```text
.
├── api/          # FastAPI route handlers
├── database/     # Database engine and session wiring
├── models/       # SQLModel table definitions
├── schemas/      # Request and response schemas
├── services/     # Business logic and placeholder AI integration
├── main.py       # FastAPI application entrypoint
├── pyproject.toml
└── uv.lock
```

## Getting Started

Install dependencies:

```bash
uv sync
```

Install dev dependencies as well:

```bash
uv sync --dev
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

- Data is stored in a local SQLite file named `database.db`.
- Interactive API docs are available at `/docs` when the server is running.
- Ruff configuration lives in `pyproject.toml`.
- Pre-commit hooks are defined in `.pre-commit-config.yaml`.
