from sqlalchemy import create_engine
from sqlmodel import Session

from core.config import settings

connect_args = {"check_same_thread": False}
engine = create_engine(settings.sqlite_url, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session
