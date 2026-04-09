import os

from sqlalchemy import create_engine
from sqlmodel import Session

sqlite_url = os.environ.get("SQLITE_URL")

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session
