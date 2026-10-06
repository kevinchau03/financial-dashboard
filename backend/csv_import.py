"""Read, clean, then load CSV uploads without mixing the three responsibilities."""
import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal

from sqlalchemy.orm import Session

TD_HEADERS = ['Date', 'Transaction', 'Debit', 'Credit', 'Balance']


def read_csv(contents: bytes, format: Literal['csv', 'td'] = 'csv') -> dict:
    """Extract UTF-8 CSV cells. TD exports have no header; keep their first row."""
    if format not in ('csv', 'td'):
        raise ValueError('Choose csv or td format.')
    reader = csv.reader(io.StringIO(contents.decode('utf-8-sig'), newline=''), strict=True)
    records = [(reader.line_num, row) for row in reader]
    if format == 'td':
        headers = TD_HEADERS.copy()
    else:
        while records and not any(cell.strip() for cell in records[0][1]):
            records.pop(0)
        if not records:
            raise ValueError('The CSV must have a header row.')
        _, headers = records.pop(0)
    return {'format': format, 'headers': headers,
            'rows': [row for _, row in records], 'line_numbers': [line for line, _ in records]}


def _parse_date(value: str) -> str:
    """Normalize both supported TD date formats to an ISO date."""
    for pattern in ('%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            continue
    raise ValueError('Date must use MM/DD/YYYY or YYYY-MM-DD.')


def _clean_amount(value: str, *, required: bool = False) -> str | None:
    if not value and not required:
        return None
    try:
        money = Decimal(value.replace(',', ''))
        if not money.is_finite() or abs(money) > Decimal('999999999.99'):
            raise InvalidOperation
        if money != money.quantize(Decimal('.01')):
            raise InvalidOperation
    except InvalidOperation:
        raise ValueError('must be a valid amount with at most two decimal places, up to 999999999.99 in magnitude.') from None
    return format(money, '.2f')


def clean_data(data: dict) -> dict:
    """Skip empty rows, validate widths, and normalize TD cells without mutating input.

    Generic CSV values retain their original text. TD whitespace is stripped,
    dates become ISO strings, amounts become exact decimal strings, and missing
    debits/credits become None. Invalid transactions reject the whole import.
    """
    format = data.get('format', 'td')
    headers = TD_HEADERS.copy() if format == 'td' else data['headers'].copy()
    rows = []
    lines = data.get('line_numbers')
    for index, raw in enumerate(data['rows']):
        if not raw or not any(cell.strip() for cell in raw):
            continue
        line = lines[index] if lines is not None else index + 1
        if len(raw) != len(headers):
            raise ValueError(f'Line {line}: expected {len(headers)} columns; found {len(raw)}.')
        if format != 'td':
            rows.append(raw.copy())
            continue
        row = [cell.strip() for cell in raw]
        try:
            row[0] = _parse_date(row[0])
        except ValueError:
            raise ValueError(f'Line {line}: date must use MM/DD/YYYY or YYYY-MM-DD. Upload a TD CSV without a header row.') from None
        if not row[1]:
            raise ValueError(f'Line {line}: transaction name is missing.')
        for column, label in ((2, 'debit and credit'), (3, 'debit and credit'), (4, 'balance')):
            try:
                row[column] = _clean_amount(row[column], required=column == 4)
            except ValueError as error:
                raise ValueError(f'Line {line}: {label} {error}') from None
        rows.append(row)
    if format == 'td' and not rows:
        raise ValueError('The TD statement contains no transactions.')
    return {'format': format, 'headers': headers, 'rows': rows}


def load_csv(data: dict, session: Session | None = None, *, filename: str | None = None,
             contents: bytes | None = None) -> dict:
    """Build recognized table columns from cleaned data and optionally persist TD rows.

    Pass a session, filename and original bytes to save one statement atomically.
    Without a session this returns the same table for preview. Keep the validated
    balance in storage for compatibility, but expose Date/Transaction/Debit/Credit.
    Generic CSVs are previewed with their own headers and are not persisted.
    """
    if data['format'] != 'td':
        return {'headers': data['headers'].copy(), 'rows': [row.copy() for row in data['rows']]}
    saved = {}
    if session is not None:
        if filename is None or contents is None:
            raise ValueError('Saving a statement requires its filename and original CSV bytes.')
        from statements import save_statement
        saved = save_statement(session, filename, contents, data['rows'])
    return {'headers': TD_HEADERS[:4], 'rows': [row[:4] for row in data['rows']], **saved}
