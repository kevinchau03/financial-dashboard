import pytest
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session
import main
from analytics import get_total_spent
from test_goals import client


def test_td_statement_preserves_first_transaction(client):
    data = b'09/24/2026,"Shop, Inc",2.39,,927.45\r\n09/23/2026,Payment,,50.00,925.06\r\n'
    response = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('statement.csv', data, 'text/csv')})
    assert response.status_code == 200
    assert response.json()['headers'] == ['Date', 'Transaction', 'Debit', 'Credit', 'Balance']
    assert response.json()['row_count'] == 2
    assert response.json()['rows'] == [['09/24/2026', 'Shop, Inc', '2.39', '', '927.45'], ['09/23/2026', 'Payment', '', '50.00', '925.06']]


@pytest.mark.parametrize('data', [b'', b'02/30/2026,Shop,1,,2', b'09/24/2026,Shop,1', b'09/24/2026,Shop,no,,2', b'09/24/2026,Shop,1,,'])
def test_invalid_td_statement(client, data):
    assert client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('statement.csv', data, 'text/csv')}).status_code == 400


def test_td_mixed_date_formats(client):
    data = b'"2026-06-08","Shop",18,,71.89\n06/09/2026,Payment,,6,77.89'
    response = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('statement.csv', data)})
    assert response.status_code == 200
    assert response.json()['stats'] == {
        'total_income': '6.00', 'total_spent': '18.00',
        'start_date': '2026-06-08', 'end_date': '2026-06-09',
    }
    with Session(main.engine) as session:
        assert session.execute(text('SELECT date FROM transactions ORDER BY id')).scalars().all() == ['2026-06-08', '2026-06-09']


@pytest.mark.parametrize('date_value', ['2026-02-30', '2026-13-01', '13/01/2026', '2026/06/08'])
def test_invalid_date_formats_save_nothing(client, date_value):
    data = f'06/08/2026,Valid,1,,2\n{date_value},Invalid,1,,3'.encode()
    response = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('statement.csv', data)})
    assert response.status_code == 400
    assert 'MM/DD/YYYY or YYYY-MM-DD' in response.json()['detail']
    with Session(main.engine) as session:
        assert session.execute(text('SELECT COUNT(*) FROM transactions')).scalar_one() == 0


def test_upload_csv(client):
    data = '\ufeffname,amount,note\r\n"Shop, Inc",001.20,"first\nsecond"\r\nOther,,<b>text</b>\r\n'
    response = client.post('/api/upload_csv', files={'file': ('budget.csv', data.encode(), 'text/csv')})
    assert response.status_code == 200
    assert response.json() == {
        'filename': 'budget.csv', 'headers': ['name', 'amount', 'note'],
        'rows': [['Shop, Inc', '001.20', 'first\nsecond'], ['Other', '', '<b>text</b>']], 'row_count': 2,
    }
    assert client.get('/api/bills').json() == []
    assert client.get('/api/goals').json() == []


@pytest.mark.parametrize('name,data,status', [
    ('test.txt', b'a\n1', 400), ('test.csv', b'', 400),
    ('test.csv', b'a,b\n1', 400), ('test.csv', b'a\n"unterminated', 400),
    ('test.csv', b'\xff', 400), ('test.csv', b'x' * (5 * 1024 * 1024 + 1), 413),
], ids=['extension', 'empty', 'columns', 'quotes', 'encoding', 'size'])
def test_invalid_upload(client, name, data, status):
    assert client.post('/api/upload_csv', files={'file': (name, data, 'text/csv')}).status_code == status


def test_headers_only_and_duplicate_headers(client):
    response = client.post('/api/upload_csv', files={'file': ('test.csv', b'a,a\n', 'text/csv')})
    assert response.status_code == 200
    assert response.json()['headers'] == ['a', 'a']
    assert response.json()['rows'] == []
    assert client.post('/api/upload_csv').status_code == 422


def test_saved_transactions_and_duplicate_upload(client):
    data = b'09/24/2026,Shop,0.10,,-1.20\n09/25/2026,Cafe,0.20,,2.00\n09/26/2026,Payment,,50.00,52.00'
    with Session(main.engine) as session:
        assert get_total_spent(session) == Decimal('0.00')
    first = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('statement.csv', data)}).json()
    assert first['already_imported'] is False
    assert first['stats'] == {
        'total_income': '50.00', 'total_spent': '0.30',
        'start_date': '2026-09-24', 'end_date': '2026-09-26',
    }
    second = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('renamed.csv', data)}).json()
    assert second['already_imported'] is True
    assert second['statement_id'] == first['statement_id']
    assert second['stats'] == first['stats']
    with Session(main.engine) as session:
        assert session.execute(text('SELECT COUNT(*) FROM statement_imports')).scalar_one() == 1
        rows = session.execute(text('SELECT date, description, debit_cents, credit_cents, balance_cents, statement_id FROM transactions ORDER BY id')).all()
        assert rows == [
            ('2026-09-24', 'Shop', 10, None, -120, first['statement_id']),
            ('2026-09-25', 'Cafe', 20, None, 200, first['statement_id']),
            ('2026-09-26', 'Payment', None, 5000, 5200, first['statement_id']),
        ]
        assert get_total_spent(session) == Decimal('0.30')
    response = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('another.csv', b'09/27/2026,Other,1.25,,53.25')})
    assert response.status_code == 200
    assert response.json()['stats'] == {
        'total_income': '50.00', 'total_spent': '1.55',
        'start_date': '2026-09-24', 'end_date': '2026-09-27',
    }
    with Session(main.engine) as session:
        assert get_total_spent(session) == Decimal('1.55')


@pytest.mark.parametrize('amount', ['0.001', '1000000000', 'NaN', 'Infinity', '1e999999'])
def test_invalid_statement_saves_nothing(client, amount):
    data = f'09/24/2026,Valid,1.20,,3.40\n09/25/2026,Invalid,{amount},,4.60'.encode()
    assert client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('invalid.csv', data)}).status_code == 400
    with Session(main.engine) as session:
        assert session.execute(text('SELECT COUNT(*) FROM statement_imports')).scalar_one() == 0
        assert session.execute(text('SELECT COUNT(*) FROM transactions')).scalar_one() == 0
