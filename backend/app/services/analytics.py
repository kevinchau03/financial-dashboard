from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import Transaction, FinancialGoal, Debts, Bills, Payment

# Analytics functions to query from uploaded csv files for budget wrapped feature

def _require_statement_id(statement_id: int) -> None:
    if type(statement_id) is not int or statement_id <= 0:
        raise ValueError('A positive statement ID is required for statement analytics.')

def get_total_spent(session: Session, statement_id: int) -> Decimal:
    """Sum debits from the selected statement only."""
    _require_statement_id(statement_id)
    total_cents = session.scalar(select(func.coalesce(func.sum(Transaction.debit_cents), 0)).where(Transaction.statement_id == statement_id))
    return (Decimal(total_cents) / 100).quantize(Decimal('0.01'))

def get_total_income(session: Session, statement_id: int) -> Decimal:
    """Sum credits from the selected statement only."""
    _require_statement_id(statement_id)
    total_cents = session.scalar(select(func.coalesce(func.sum(Transaction.credit_cents), 0)).where(Transaction.statement_id == statement_id))
    return (Decimal(total_cents) / 100).quantize(Decimal('0.01'))

def get_time_range(session: Session, statement_id: int) -> tuple[str | None, str | None]:
    """Return the selected statement's date range."""
    _require_statement_id(statement_id)
    start_date, end_date = session.execute(select(func.min(Transaction.date), func.max(Transaction.date)).where(Transaction.statement_id == statement_id)).one()
    return str(start_date) if start_date else None, str(end_date) if end_date else None

def get_total_transactions(session: Session, statement_id: int) -> int:
    """Count the selected statement's transactions."""
    _require_statement_id(statement_id)
    total_count = session.scalar(select(func.count(Transaction.id)).where(Transaction.statement_id == statement_id))
    return total_count

def get_most_frequent_transaction_name(session: Session, statement_id: int) -> dict | None:
    """Return the most frequent exact description and its occurrence count for one statement."""
    _require_statement_id(statement_id)
    result = session.execute(select(Transaction.description, func.count(Transaction.id).label('occurrence_count'))
        .where(Transaction.statement_id == statement_id).group_by(Transaction.description)
        .order_by(func.count(Transaction.id).desc(), Transaction.description).limit(1)).mappings().one_or_none()
    return {'name': result['description'], 'count': result['occurrence_count']} if result else None

def get_largest_transaction(session: Session, statement_id: int) -> dict | None:
    """Return the largest debit or credit with its direction and transaction details.

    Ties choose the earliest date, then original transaction order, then debit.
    Amounts are decimal strings so the API never converts money to floats.
    """
    _require_statement_id(statement_id)
    # Two ORM queries keep tenant filtering on both sides of the comparison.
    choices = []
    for kind, column in [('debit', Transaction.debit_cents), ('credit', Transaction.credit_cents)]:
        row = session.execute(select(Transaction.id, Transaction.date, Transaction.description, column.label('amount_cents'))
            .where(Transaction.statement_id == statement_id, column.is_not(None))
            .order_by(column.desc(), Transaction.date, Transaction.id).limit(1)).mappings().one_or_none()
        if row:
            choices.append({**row, 'kind': kind})
    row = min(choices, key=lambda row: (-row['amount_cents'], row['date'], row['id'], row['kind'] != 'debit')) if choices else None
    if row is None:
        return None
    return {'id': row['id'], 'date': str(row['date']), 'description': row['description'],
            'amount': format(Decimal(row['amount_cents']) / 100, '.2f'), 'kind': row['kind']}


def get_highest_spending_day(session: Session, statement_id: int) -> dict | None:
    """Return the highest positive-debit day, its spending total and all its transactions.

    Credits appear in the breakdown but do not reduce the spending total.
    Equal spending totals choose the earliest date.
    """
    _require_statement_id(statement_id)
    day = session.execute(select(Transaction.date, func.sum(Transaction.debit_cents).label('total_cents'))
        .where(Transaction.statement_id == statement_id, Transaction.debit_cents > 0)
        .group_by(Transaction.date).order_by(func.sum(Transaction.debit_cents).desc(), Transaction.date).limit(1)).mappings().one_or_none()
    if day is None:
        return None
    rows = session.execute(select(Transaction.id, Transaction.description, Transaction.debit_cents, Transaction.credit_cents)
        .where(Transaction.statement_id == statement_id, Transaction.date == day['date']).order_by(Transaction.id)).mappings().all()

    def money(cents):
        return format(Decimal(cents) / 100, '.2f') if cents is not None else None

    return {'date': str(day['date']), 'total_spent': money(day['total_cents']),
            'transactions': [{'id': row['id'], 'description': row['description'],
                              'debit': money(row['debit_cents']), 'credit': money(row['credit_cents'])}
                             for row in rows]}

# Helper functions to query the database for totals across financial goals, debts, and bills

def get_total_savings(session: Session) -> Decimal:
    total = session.scalar(select(func.coalesce(func.sum(FinancialGoal.current_amount), 0)))
    return Decimal(str(total)).quantize(Decimal("0.01"))

def get_total_goal_contributions(session: Session) -> Decimal:
    """Total active goal payments; opening balances are not contributions."""
    total = session.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.kind == 'goal', Payment.undone_at.is_(None)))
    return Decimal(str(total)).quantize(Decimal("0.01"))

def get_total_debt(session: Session) -> Decimal:
    """Total the remaining balance across all debts."""
    total = session.scalar(select(func.coalesce(func.sum(Debts.amount - Debts.current_amount), 0)))
    return Decimal(str(total)).quantize(Decimal("0.01"))

def get_total_bills(session: Session) -> Decimal:
    """Total the amounts recorded in all bills."""
    total = session.scalar(select(func.coalesce(func.sum(Bills.amount), 0)))
    return Decimal(str(total)).quantize(Decimal("0.01"))
