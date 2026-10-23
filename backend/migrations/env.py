"""Run explicit PostgreSQL migrations; application startup never changes schema."""
from alembic import context
from app.database import Base, build_engine
from app import models
import os

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    # Supabase-only ownership constraints intentionally live in PostgreSQL, not
    # SQLite model metadata. Preserve them during future autogeneration.
    if reflected and compare_to is None and name:
        if type_ == 'foreign_key_constraint' and name.startswith('fk_') and name.endswith(('_auth_user', '_owner')):
            return False
        if type_ == 'unique_constraint' and name.startswith('uq_') and name.endswith('_owner_id'):
            return False
    return True


def run_migrations_online():
    url = os.getenv('MIGRATION_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not url:
        raise RuntimeError('Set DATABASE_URL before running migrations.')
    engine = build_engine(url)
    if engine.dialect.name != 'postgresql':
        raise RuntimeError('These migrations target Supabase PostgreSQL; SQLite is for disposable tests.')
    try:
        with engine.connect() as connection:
            connection = connection.execution_options(hide_parameters=True)
            context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
            with context.begin_transaction():
                # Serialize deployments applying the same migrations.
                connection.exec_driver_sql('SELECT pg_advisory_xact_lock(6026102201)')
                context.run_migrations()
                connection.exec_driver_sql('ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY')
                connection.exec_driver_sql('REVOKE ALL ON alembic_version FROM anon, authenticated')
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError('Use an online migration against the intended PostgreSQL project.')
else:
    run_migrations_online()
