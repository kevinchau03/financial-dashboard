"""Shared ledger writer. The calling workflow owns the transaction and balance rules."""
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.models import Payment


def add_payment(session: Session, *, kind: str, target, amount: Decimal,
                paid_on: date, source: str = 'manual', allocation_id: int | None = None):
    payment = Payment(kind=kind, target_name=target.name,
                      **{f'{kind}_id': target.id}, amount=amount, paid_on=paid_on,
                      due_date=target.due_date, source=source, allocation_id=allocation_id,
                      recorded_at=datetime.now(timezone.utc))
    session.add(payment)
    return payment


def detach_payments(session: Session, kind: str, target_id: int):
    column = {'bill': Payment.bill_id, 'debt': Payment.debt_id, 'goal': Payment.goal_id}[kind]
    session.execute(update(Payment).where(column == target_id).values({column.key: None}))
