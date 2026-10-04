"""Store validated TD statement rows together in one database transaction."""
from decimal import Decimal
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import StatementImport, Transaction
from analytics import parse_statement_date


def save_statement(session: Session, filename: str, contents: bytes, rows: list[list[str]]) -> dict:
    content_hash = sha256(contents).hexdigest()
    existing_query = select(StatementImport).where(StatementImport.content_hash == content_hash)
    existing = session.scalar(existing_query)
    if existing:
        return {'statement_id': existing.id, 'already_imported': True}

    def cents(value: str) -> int | None:
        return int(Decimal(value.replace(',', '')) * 100) if value else None

    statement = StatementImport(filename=filename, content_hash=content_hash)
    try:
        session.add(statement)
        session.flush()
        for row in rows:
            session.add(Transaction(
                statement_id=statement.id,
                date=parse_statement_date(row[0]),
                description=row[1], debit_cents=cents(row[2]),
                credit_cents=cents(row[3]), balance_cents=cents(row[4]),
            ))
        session.commit()
    except IntegrityError:
        session.rollback()
        # A simultaneous upload may have saved this same file first.
        existing = session.scalar(existing_query)
        if existing:
            return {'statement_id': existing.id, 'already_imported': True}
        raise
    return {'statement_id': statement.id, 'already_imported': False}
