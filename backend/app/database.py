from pathlib import Path
import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


@event.listens_for(Engine, 'connect')
def enable_sqlite_foreign_keys(connection, _):
    if isinstance(connection, sqlite3.Connection):
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


engine = create_engine(
    f"sqlite:///{(Path(__file__).resolve().parent.parent / 'goals.db').as_posix()}",
    connect_args={"check_same_thread": False},
)


def get_session():
    with Session(engine) as session:
        yield session
