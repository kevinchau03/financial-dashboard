"""Versioned SQLite upgrade from separate payment tables to the unified ledger.

Copy, backfill, and retire legacy tables in one transaction, without changing balances.
Run before serving requests; migration errors abort startup rather than losing history.
"""
from decimal import Decimal
from sqlalchemy import MetaData, Table, inspect, select, text
from app.models import Payment, PaychequeAllocation, FinancialGoal

VERSION = '20261020_unified_payments'


def migrate_payments(engine):
    with engine.begin() as connection:
        # Explicitly begin SQLite DDL transaction (pysqlite otherwise defers BEGIN).
        if engine.dialect.name == 'sqlite':
            connection.exec_driver_sql('BEGIN IMMEDIATE')
        connection.execute(text('CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(80) PRIMARY KEY)'))
        if connection.scalar(text('SELECT version FROM schema_migrations WHERE version = :version'), {'version': VERSION}):
            return
        tables = set(inspect(connection).get_table_names())
        for kind, table_name, target_table in [('bill', 'bill_payments', 'bills'), ('debt', 'debt_payments', 'debts')]:
            if table_name not in tables:
                continue
            metadata = MetaData()
            old = Table(table_name, metadata, autoload_with=connection)
            target = Table(target_table, metadata, autoload_with=connection)
            column = f'{kind}_id'
            rows = connection.execute(select(old, target.c.name.label('target_name')).select_from(
                old.outerjoin(target, old.c[column] == target.c.id))).mappings()
            for row in rows:
                connection.execute(Payment.__table__.insert().values(
                    kind=kind, target_name=row['target_name'] or f'Deleted {kind}',
                    **{column: row[column] if row['target_name'] is not None else None},
                    amount=row['amount'], paid_on=row['paid_on'], due_date=row['due_date'], source='legacy'))
        # Completed debt allocations already have debt payment rows. Only goals
        # need backfill; opening balances and deleted plans cannot be reconstructed.
        allocations = PaychequeAllocation.__table__
        goals = FinancialGoal.__table__
        rows = connection.execute(select(allocations, goals.c.id.label('existing_goal_id')).select_from(
            allocations.outerjoin(goals, allocations.c.goal_id == goals.c.id)).where(
            allocations.c.kind == 'goal', allocations.c.status == 'completed')).mappings()
        for row in rows:
            if row['completed_on'] is None:
                raise ValueError('Completed goal allocation has no completion date; repair it before migration.')
            connection.execute(Payment.__table__.insert().values(
                kind='goal', target_name=row['name'], goal_id=row['existing_goal_id'],
                amount=Decimal(row['amount_cents']) / 100, paid_on=row['completed_on'],
                due_date=None, source='paycheque', allocation_id=row['id']))
        for table_name in ('bill_payments', 'debt_payments'):
            if table_name in tables:
                connection.execute(text(f'DROP TABLE {table_name}'))
        connection.execute(text('INSERT INTO schema_migrations (version) VALUES (:version)'), {'version': VERSION})
