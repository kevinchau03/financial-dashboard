from decimal import Decimal
from datetime import date, datetime
from decimal import InvalidOperation
import csv
import io

from sqlalchemy import text
from sqlalchemy.orm import Session

# Read CSV file and return a list of dictionaries
def read_csv(contents: bytes) -> dict:
    """Parse uploaded UTF-8 CSV bytes without saving the file to disk."""
    reader = csv.reader(io.StringIO(contents.decode('utf-8-sig'), newline=''), strict=True)
    headers = next(reader, None)
    if not headers or not any(header.strip() for header in headers):
        raise ValueError('The CSV must have a header row.')
    rows = []
    for row in reader:
        if not row:
            continue
        if len(row) != len(headers):
            raise ValueError(f'CSV record ending on line {reader.line_num} has {len(row)} values; expected {len(headers)}.')
        rows.append(row)
    return {'headers': headers, 'rows': rows}

def parse_statement_date(value: str) -> date:
    """Accept both date formats used by TD CSV exports."""
    for date_format in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    raise ValueError('Date must use MM/DD/YYYY or YYYY-MM-DD.')


# Analytics functions
def read_td_csv(contents: bytes) -> dict:
    """Read TD's headerless date, transaction, debit, credit, balance export."""
    reader = csv.reader(io.StringIO(contents.decode('utf-8-sig'), newline=''), strict=True)
    rows = []
    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        line = reader.line_num
        if len(row) != 5:
            raise ValueError(f'Line {line}: expected 5 columns: date, transaction, debit, credit, balance.')
        row = [cell.strip() for cell in row]
        try:
            parse_statement_date(row[0])
        except ValueError:
            raise ValueError(f'Line {line}: date must use MM/DD/YYYY or YYYY-MM-DD. Upload a TD CSV without a header row.')
        if not row[1]:
            raise ValueError(f'Line {line}: transaction name is missing.')
        for index, label in [(2, 'debit'), (3, 'credit'), (4, 'balance')]:
            if not row[index] and index != 4:
                continue
            try:
                value = Decimal(row[index].replace(',', ''))
                if not value.is_finite():
                    raise InvalidOperation
                if abs(value) > Decimal('999999999.99') or value != value.quantize(Decimal('0.01')):
                    raise InvalidOperation
            except InvalidOperation:
                raise ValueError(f'Line {line}: {label} must be a valid amount with at most two decimal places, up to 999999999.99 in magnitude.')
        rows.append(row)
    if not rows:
        raise ValueError('The TD statement contains no transactions.')
    return {'headers': ['Date', 'Transaction', 'Debit', 'Credit', 'Balance'], 'rows': rows}

# Analytics functions to query the database for totals and ranges from statements

def get_total_spent(session: Session) -> Decimal:
    """Sum debits across saved statements; credits are not subtracted."""
    query = text("""
        SELECT COALESCE(SUM(debit_cents), 0)
        FROM transactions
    """)
    total_cents = session.execute(query).scalar_one()
    return (Decimal(total_cents) / 100).quantize(Decimal('0.01'))

def get_total_income(session: Session) -> Decimal:
    """Sum credits across saved statements; debits are not subtracted."""
    query = text("""
        SELECT COALESCE(SUM(credit_cents), 0)
        FROM transactions
    """)
    total_cents = session.execute(query).scalar_one()
    return (Decimal(total_cents) / 100).quantize(Decimal('0.01'))

def get_time_range(session: Session) -> tuple[datetime | None, datetime | None]:
    """Return the earliest and latest transaction dates across all saved statements."""
    query = text("""
        SELECT MIN(date), MAX(date)
        FROM transactions
    """)
    return session.execute(query).one()


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
