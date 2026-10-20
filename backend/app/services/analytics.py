from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

# Analytics functions to query from uploaded csv files for budget wrapped feature

def _require_statement_id(statement_id: int) -> None:
    if type(statement_id) is not int or statement_id <= 0:
        raise ValueError('A positive statement ID is required for statement analytics.')

def get_total_spent(session: Session, statement_id: int) -> Decimal:
    """Sum debits from the selected statement only."""
    _require_statement_id(statement_id)
    query = text("""
        SELECT COALESCE(SUM(debit_cents), 0)
        FROM transactions
        WHERE statement_id = :statement_id
    """)
    total_cents = session.execute(query, {'statement_id': statement_id}).scalar_one()
    return (Decimal(total_cents) / 100).quantize(Decimal('0.01'))

def get_total_income(session: Session, statement_id: int) -> Decimal:
    """Sum credits from the selected statement only."""
    _require_statement_id(statement_id)
    query = text("""
        SELECT COALESCE(SUM(credit_cents), 0)
        FROM transactions
        WHERE statement_id = :statement_id
    """)
    total_cents = session.execute(query, {'statement_id': statement_id}).scalar_one()
    return (Decimal(total_cents) / 100).quantize(Decimal('0.01'))

def get_time_range(session: Session, statement_id: int) -> tuple[str | None, str | None]:
    """Return the selected statement's date range."""
    _require_statement_id(statement_id)
    query = text("""
        SELECT MIN(date), MAX(date)
        FROM transactions
        WHERE statement_id = :statement_id
    """)
    start_date, end_date = session.execute(query, {'statement_id': statement_id}).one()
    return start_date, end_date

def get_total_transactions(session: Session, statement_id: int) -> int:
    """Count the selected statement's transactions."""
    _require_statement_id(statement_id)
    query = text("""
        SELECT COUNT(*)
        FROM transactions
        WHERE statement_id = :statement_id
    """)
    total_count = session.execute(query, {'statement_id': statement_id}).scalar_one()
    return total_count

def get_most_frequent_transaction_name(session: Session, statement_id: int) -> dict | None:
    """Return the most frequent exact description and its occurrence count for one statement."""
    _require_statement_id(statement_id)
    query = text("""
        SELECT description, COUNT(*) AS occurrence_count
        FROM transactions
        WHERE statement_id = :statement_id
        GROUP BY description
        ORDER BY COUNT(*) DESC, description ASC
        LIMIT 1
    """)
    result = session.execute(query, {'statement_id': statement_id}).mappings().one_or_none()
    return {'name': result['description'], 'count': result['occurrence_count']} if result else None

def get_largest_transaction(session: Session, statement_id: int) -> dict | None:
    """Return the largest debit or credit with its direction and transaction details.

    Ties choose the earliest date, then original transaction order, then debit.
    Amounts are decimal strings so the API never converts money to floats.
    """
    _require_statement_id(statement_id)
    query = text("""
        SELECT id, date, description, amount_cents, kind
        FROM (
            SELECT id, date, description, debit_cents AS amount_cents, 'debit' AS kind
            FROM transactions WHERE statement_id = :statement_id AND debit_cents IS NOT NULL
            UNION ALL
            SELECT id, date, description, credit_cents AS amount_cents, 'credit' AS kind
            FROM transactions WHERE statement_id = :statement_id AND credit_cents IS NOT NULL
        ) AS movements
        ORDER BY amount_cents DESC, date ASC, id ASC,
                 CASE WHEN kind = 'debit' THEN 0 ELSE 1 END
        LIMIT 1
    """)
    row = session.execute(query, {'statement_id': statement_id}).mappings().one_or_none()
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
    query = text("""
        SELECT date, SUM(debit_cents) AS total_cents
        FROM transactions
        WHERE statement_id = :statement_id AND debit_cents > 0
        GROUP BY date
        ORDER BY SUM(debit_cents) DESC, date ASC
        LIMIT 1
    """)
    day = session.execute(query, {'statement_id': statement_id}).mappings().one_or_none()
    if day is None:
        return None
    rows = session.execute(text("""
        SELECT id, description, debit_cents, credit_cents
        FROM transactions
        WHERE statement_id = :statement_id AND date = :date
        ORDER BY id
    """), {'statement_id': statement_id, 'date': day['date']}).mappings().all()

    def money(cents):
        return format(Decimal(cents) / 100, '.2f') if cents is not None else None

    return {'date': str(day['date']), 'total_spent': money(day['total_cents']),
            'transactions': [{'id': row['id'], 'description': row['description'],
                              'debit': money(row['debit_cents']), 'credit': money(row['credit_cents'])}
                             for row in rows]}

# Helper functions to query the database for totals across financial goals, debts, and bills

def get_total_savings(session: Session) -> Decimal:
    query = text("""
        SELECT COALESCE(SUM(current_amount), 0)
        FROM financial_goals
    """)

    total = session.execute(query).scalar_one()
    return Decimal(str(total)).quantize(Decimal("0.01"))

def get_total_goal_contributions(session: Session) -> Decimal:
    """Total the contributions recorded in all goals."""
    query = text(
        """
        SELECT COALESCE(SUM(total_contributions), 0)
        FROM financial_goals
        """
    )
    total = session.execute(query).scalar_one()
    return Decimal(str(total)).quantize(Decimal("0.01"))

def get_total_debt(session: Session) -> Decimal:
    """Total the remaining balance across all debts."""
    query = text(
        """
        SELECT COALESCE(SUM(amount - current_amount), 0)
        FROM debts
        """
    )
    total = session.execute(query).scalar_one()
    return Decimal(str(total)).quantize(Decimal("0.01"))

def get_total_bills(session: Session) -> Decimal:
    """Total the amounts recorded in all bills."""
    query = text(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM bills
        """
    )
    total = session.execute(query).scalar_one()
    return Decimal(str(total)).quantize(Decimal("0.01"))
