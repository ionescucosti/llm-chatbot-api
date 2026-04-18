"""
Test configuration and fixtures.

Uses SQLite in-memory database for test isolation.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlmodel import Session, SQLModel

# Set test environment variables BEFORE importing app/settings
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DEFAULT_LANGUAGE"] = "en"

from database.db import get_session
from main import app


@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh database session for each test."""
    # Use StaticPool to share the same in-memory database across connections
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with overridden database session."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
