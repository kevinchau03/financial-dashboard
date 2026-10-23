"""Existing additive SQLite compatibility upgrades; preserves stored data."""
from sqlalchemy import inspect, text
from app.database import Base
from app import models  # Register all tables before creating metadata.


def initialize_database(engine, *, legacy_owner=None):
    if engine.dialect.name != 'sqlite':
        raise RuntimeError('Run alembic upgrade head to initialize PostgreSQL.')
    # Existing single-user SQLite files are only claimed by an explicitly named
    # owner. The Supabase setup never opens or changes the original SQLite file.
    existing = inspect(engine).get_table_names()
    legacy_tables = [table.name for table in Base.metadata.sorted_tables if table.name in existing
                     and 'user_id' not in {c['name'] for c in inspect(engine).get_columns(table.name)}]
    if legacy_tables and legacy_owner is None:
        raise RuntimeError('Legacy SQLite database: use a fresh database or an explicit ownership migration.')
    if legacy_owner is not None:
        from uuid import UUID
        owner = UUID(str(legacy_owner)).hex
        with engine.begin() as connection:
            for name in legacy_tables:
                connection.execute(text(f'ALTER TABLE {name} ADD COLUMN user_id CHAR(32)'))
                connection.execute(text(f'UPDATE {name} SET user_id = :owner WHERE user_id IS NULL'), {'owner': owner})
    Base.metadata.create_all(engine)
    payment_columns = {column['name'] for column in inspect(engine).get_columns('payments')}
    with engine.begin() as connection:
        for name, definition in {
            'undo_state': 'JSON',
            'undo_account_id': 'INTEGER REFERENCES accounts(id) ON DELETE SET NULL',
            'undone_at': 'DATETIME',
        }.items():
            if name not in payment_columns:
                connection.execute(text(f'ALTER TABLE payments ADD COLUMN {name} {definition}'))
    if 'account_id' not in {column['name'] for column in inspect(engine).get_columns('financial_goals')}:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE financial_goals ADD COLUMN account_id INTEGER REFERENCES accounts(id)'))
    if 'account_id' not in {column['name'] for column in inspect(engine).get_columns('paycheque_allocations')}:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE paycheque_allocations ADD COLUMN account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL'))
    paycheque_columns = {column['name'] for column in inspect(engine).get_columns('paycheques')}
    with engine.begin() as connection:
        for name, definition in {'bills_reserved': 'NUMERIC NOT NULL DEFAULT 0', 'spending_reserved': 'NUMERIC NOT NULL DEFAULT 0', 'next_payday': 'DATE', 'received_on': 'DATE', 'allocated_cents': 'INTEGER NOT NULL DEFAULT 0',
                                 'request_id': 'VARCHAR(36)', 'request_fingerprint': 'VARCHAR(64)'}.items():
            if name not in paycheque_columns:
                connection.execute(text(f'ALTER TABLE paycheques ADD COLUMN {name} {definition}'))
        connection.execute(text('DROP INDEX IF EXISTS ix_paycheques_request_id'))
        connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_paycheques_user_request ON paycheques(user_id, request_id)'))
    if 'csv_contents' not in {column['name'] for column in inspect(engine).get_columns('statement_imports')}:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE statement_imports ADD COLUMN csv_contents BLOB'))
    if "recurrence_day" not in {column["name"] for column in inspect(engine).get_columns("bills")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE bills ADD COLUMN recurrence_day INTEGER"))
    # Add the new field to existing SQLite databases without replacing user data.
    if "is_paid" not in {column["name"] for column in inspect(engine).get_columns("bills")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE bills ADD COLUMN is_paid BOOLEAN NOT NULL DEFAULT 0"))
    from app.payment_migration import migrate_payments
    migrate_payments(engine, legacy_owner=legacy_owner)
