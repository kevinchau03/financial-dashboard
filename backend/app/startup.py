"""Existing additive SQLite compatibility upgrades; preserves stored data."""
from sqlalchemy import inspect, text
from app.database import Base
from app import models  # Register all tables before creating metadata.


def initialize_database(engine):
    Base.metadata.create_all(engine)
    paycheque_columns = {column['name'] for column in inspect(engine).get_columns('paycheques')}
    with engine.begin() as connection:
        for name, definition in {'received_on': 'DATE', 'allocated_cents': 'INTEGER NOT NULL DEFAULT 0',
                                 'request_id': 'VARCHAR(36)', 'request_fingerprint': 'VARCHAR(64)'}.items():
            if name not in paycheque_columns:
                connection.execute(text(f'ALTER TABLE paycheques ADD COLUMN {name} {definition}'))
        connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_paycheques_request_id ON paycheques(request_id)'))
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
