from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

# Analytics functions to query the database for totals and ranges from statements

def get_total_spent(session: Session, statement_id: int | None = None) -> Decimal:
    """Sum one statement's debits, or all saved debits when no ID is supplied."""
    query = text("""
        SELECT COALESCE(SUM(debit_cents), 0)
        FROM transactions
        WHERE (:statement_id IS NULL OR statement_id = :statement_id)
    """)
    total_cents = session.execute(query, {'statement_id': statement_id}).scalar_one()
    return (Decimal(total_cents) / 100).quantize(Decimal('0.01'))

def get_total_income(session: Session, statement_id: int | None = None) -> Decimal:
    """Sum one statement's credits, or all saved credits when no ID is supplied."""
    query = text("""
        SELECT COALESCE(SUM(credit_cents), 0)
        FROM transactions
        WHERE (:statement_id IS NULL OR statement_id = :statement_id)
    """)
    total_cents = session.execute(query, {'statement_id': statement_id}).scalar_one()
    return (Decimal(total_cents) / 100).quantize(Decimal('0.01'))

def get_time_range(session: Session, statement_id: int | None = None) -> tuple[str | None, str | None]:
    """Return one statement's date range, or all saved dates when no ID is supplied."""
    query = text("""
        SELECT MIN(date), MAX(date)
        FROM transactions
        WHERE (:statement_id IS NULL OR statement_id = :statement_id)
    """)
    start_date, end_date = session.execute(query, {'statement_id': statement_id}).one()
    return start_date, end_date


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
