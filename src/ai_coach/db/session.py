from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session

from ai_coach.config.settings import settings

engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


@contextmanager
def session_scope():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def get_db():
    with Session(engine) as session:
        yield session
