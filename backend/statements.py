"""Store validated TD statement rows together in one database transaction."""
from decimal import Decimal
from datetime import date
from hashlib import sha256

from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import StatementImport, Transaction
from database import get_session
from analytics import get_total_income, get_total_spent, get_time_range

router = APIRouter(prefix='/api/statements', tags=['statements'])


def save_statement(session: Session, filename: str, contents: bytes, rows: list[list[str | None]]) -> dict:
    content_hash = sha256(contents).hexdigest()
    existing_query = select(StatementImport).where(StatementImport.content_hash == content_hash)
    existing = session.scalar(existing_query)
    if existing:
        if existing.csv_contents is None:
            existing.csv_contents = contents
            session.commit()
        return {'statement_id': existing.id, 'already_imported': True}

    def cents(value: str | None) -> int | None:
        return int(Decimal(value) * 100) if value is not None else None

    statement = StatementImport(filename=filename, content_hash=content_hash, csv_contents=contents)
    try:
        session.add(statement)
        session.flush()
        for row in rows:
            session.add(Transaction(
                statement_id=statement.id,
                date=date.fromisoformat(row[0]),
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


@router.get('')
def list_statements(session: Annotated[Session, Depends(get_session)],
                    offset: Annotated[int, Query(ge=0)] = 0,
                    limit: Annotated[int, Query(ge=1, le=100)] = 20):
    records = session.execute(select(
        StatementImport.id, StatementImport.filename, StatementImport.imported_at,
        StatementImport.csv_contents.is_not(None),
        func.count(Transaction.id), func.min(Transaction.date), func.max(Transaction.date),
    ).outerjoin(Transaction, Transaction.statement_id == StatementImport.id)
      .group_by(StatementImport.id)
      .order_by(StatementImport.imported_at.desc(), StatementImport.id.desc())
      .offset(offset).limit(limit)).all()
    return {
        'items': [{
            'statement_id': statement_id, 'filename': filename,
            'imported_at': imported_at, 'row_count': count,
            'start_date': start, 'end_date': end, 'has_file': has_file,
        } for statement_id, filename, imported_at, has_file, count, start, end in records],
        'total': session.scalar(select(func.count()).select_from(StatementImport)),
    }


def find_statement(session: Session, statement_id: int) -> StatementImport:
    statement = session.get(StatementImport, statement_id)
    if statement is None:
        raise HTTPException(404, 'Statement not found.')
    return statement


@router.get('/{statement_id}')
def read_statement(statement_id: int, session: Annotated[Session, Depends(get_session)]):
    statement = find_statement(session, statement_id)
    transactions = session.scalars(select(Transaction).where(
        Transaction.statement_id == statement_id,
    ).order_by(Transaction.id)).all()

    def money(cents: int | None) -> str | None:
        return format(Decimal(cents) / 100, '.2f') if cents is not None else None

    start, end = get_time_range(session, statement_id)
    return {
        'statement_id': statement.id, 'filename': statement.filename,
        'imported_at': statement.imported_at, 'has_file': statement.csv_contents is not None,
        'headers': ['Date', 'Transaction', 'Debit', 'Credit'],
        'rows': [[row.date.isoformat(), row.description, money(row.debit_cents), money(row.credit_cents)] for row in transactions],
        'row_count': len(transactions),
        'stats': {'total_income': str(get_total_income(session, statement_id)),
                  'total_spent': str(get_total_spent(session, statement_id)),
                  'start_date': start, 'end_date': end},
    }


@router.get('/{statement_id}/summary')
def statement_summary(statement_id: int, session: Annotated[Session, Depends(get_session)]):
    statement = find_statement(session, statement_id)
    start, end = get_time_range(session, statement_id)
    return {
        'statement_id': statement.id,
        'stats': {'total_income': str(get_total_income(session, statement_id)),
                  'total_spent': str(get_total_spent(session, statement_id)),
                  'start_date': start, 'end_date': end},
    }


@router.get('/{statement_id}/file')
def download_statement(statement_id: int, session: Annotated[Session, Depends(get_session)]):
    statement = find_statement(session, statement_id)
    if statement.csv_contents is None:
        raise HTTPException(404, 'The original CSV was not retained for this older upload. Re-upload it to save the file.')
    return Response(content=statement.csv_contents, media_type='text/csv', headers={
        'Content-Disposition': f"attachment; filename*=UTF-8''{quote(statement.filename, safe='')}",
        'X-Content-Type-Options': 'nosniff',
    })
