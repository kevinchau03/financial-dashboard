from typing import Annotated
from uuid import UUID
import sqlite3
from fastapi import Depends, HTTPException
from sqlalchemy import create_engine, event, text, inspect
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column, with_loader_criteria
from sqlalchemy.pool import NullPool
from app.config import database_url
from app.auth import AuthUser, get_current_user


class Base(DeclarativeBase):
    pass


class Owned:
    # Supabase Auth and composite ownership foreign keys are installed by the
    # PostgreSQL migration; SQLite fixtures do not have an auth.users schema.
    user_id: Mapped[UUID] = mapped_column(index=True)


def build_engine(database_url: str) -> Engine:
    url = make_url(database_url)
    if url.get_backend_name() == 'sqlite':
        return create_engine(url, connect_args={'check_same_thread': False})
    if url.get_backend_name() not in ('postgres', 'postgresql'):
        raise ValueError('DATABASE_URL must use PostgreSQL or SQLite.')
    url = url.set(drivername='postgresql+psycopg')
    return create_engine(url, poolclass=NullPool, hide_parameters=True,
                         connect_args={'sslmode': 'require', 'prepare_threshold': None, 'connect_timeout': 10})


@event.listens_for(Engine, 'connect')
def enable_sqlite_foreign_keys(connection, _):
    if isinstance(connection, sqlite3.Connection):
        connection.execute('PRAGMA foreign_keys=ON')


engine = build_engine(database_url())


class UserSession(Session):
    """One immutable owner per request; ORM filtering plus PostgreSQL RLS."""
    def __init__(self, *args, user_id: UUID, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_id = UUID(str(user_id))

    @property
    def user_id(self) -> UUID:
        return self._user_id


@event.listens_for(UserSession, 'after_begin')
def set_database_identity(session, transaction, connection):
    if connection.dialect.name == 'postgresql':
        connection.execute(text('SET LOCAL ROLE financial_app'))
        connection.execute(text("SELECT set_config('app.user_id', :user_id, true)"), {'user_id': str(session.user_id)})


@event.listens_for(UserSession, 'do_orm_execute')
def scope_queries(state):
    if not state.is_orm_statement:
        raise RuntimeError('UserSession requires ORM statements; raw SQL belongs in reviewed migrations.')
    if state.is_insert:
        raise RuntimeError('Create records with session.add so ownership and references are validated.')
    if state.is_update and any(getattr(key, 'key', key) == 'user_id' for key in (state.statement._values or {})):
        raise RuntimeError('Record ownership cannot be changed.')
    owner = state.session.user_id
    state.statement = state.statement.options(with_loader_criteria(
        Owned, lambda model: model.user_id == owner, include_aliases=True,
    ))


@event.listens_for(UserSession, 'before_flush')
def scope_writes(session, *_):
    references = {mapper.local_table.name: mapper.class_ for mapper in Base.registry.mappers}
    for row in set(session.new) | set(session.dirty) | set(session.deleted):
        if not isinstance(row, Owned):
            raise RuntimeError('Unscoped record in authenticated session.')
        if row in session.new and row.user_id is None:
            row.user_id = session.user_id
        if row.user_id != session.user_id or inspect(row).attrs.user_id.history.deleted:
            raise HTTPException(404, 'Record not found.')
        if row in session.deleted:
            continue
        for column in row.__table__.columns:
            for fk in column.foreign_keys:
                target = references.get(fk.column.table.name)
                value = getattr(row, column.key)
                if target and value is not None and session.get(target, value) is None:
                    raise HTTPException(404, 'Related record not found.')


def get_session(user: Annotated[AuthUser, Depends(get_current_user)]):
    with UserSession(engine, user_id=user.id) as session:
        yield session
