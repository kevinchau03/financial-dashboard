from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


engine = create_engine(
    f"sqlite:///{(Path(__file__).resolve().parent.parent / 'goals.db').as_posix()}",
    connect_args={"check_same_thread": False},
)


def get_session():
    with Session(engine) as session:
        yield session
