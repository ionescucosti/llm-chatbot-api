from sqlalchemy import create_engine
from sqlmodel import Session

from core.config import settings

engine = create_engine(settings.database_url)


def get_session():
    with Session(engine) as session:
        yield session
