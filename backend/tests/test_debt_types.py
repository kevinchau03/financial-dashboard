from datetime import date
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.startup import initialize_database


@pytest.mark.parametrize('kind', ['credit_card', 'line_of_credit', 'personal_loan', 'auto_loan', 'student_loan', 'mortgage', 'buy_now_pay_later', 'personal_debt'])
def test_debt_type_metadata_and_payments(client, kind):
    revolving = kind in ('credit_card', 'line_of_credit')
    metadata = ({'credit_limit': '2000.00', 'minimum_payment': '25.00'} if revolving else
                {'payment_amount': '100.00', 'payment_frequency': 'biweekly'})
    response = client.post('/api/debts', json={
        'name': kind, 'amount': '1000.00', 'debt_type': kind,
        'due_date': '2027-01-15', **metadata,
    })
    assert response.status_code == 201, response.text
    debt = response.json()
    assert debt['debt_type'] == kind
    for field, value in metadata.items():
        assert debt[field] == value
    url = f"/api/debts/{debt['id']}"
    payment = client.post(url + '/payments', json={'amount': '50', 'paid_on': str(date.today())})
    assert payment.status_code == 201
    assert payment.json()['remaining_amount'] == '950.00'
    assert payment.json()['due_date'] == '2027-01-15'  # Reference schedule never advances automatically.
    # Old clients may edit names/balances without supplying the new metadata.
    edited = client.put(url, json={'name': 'Renamed', 'amount': '1000.00'})
    assert edited.status_code == 200, edited.text
    assert edited.json()['debt_type'] == kind
    assert edited.json()['payments'] == payment.json()['payments']
    for field, value in metadata.items():
        assert edited.json()[field] == value
    # Metadata edits can also omit type; validate against the stored type.
    changes = {'minimum_payment': '30.00'} if revolving else {'payment_amount': '75.00'}
    changed = client.put(url, json={'name': 'Renamed', 'amount': '1000.00', **changes})
    assert changed.status_code == 200, changed.text
    for field, value in changes.items():
        assert changed.json()[field] == value


@pytest.mark.parametrize('changes', [
    {'debt_type': 'other'}, {'debt_type': 'unknown'},
    {'debt_type': 'credit_card', 'credit_limit': '0'},
    {'debt_type': 'credit_card', 'credit_limit': '-1'},
    {'debt_type': 'credit_card', 'credit_limit': '10.001'},
    {'debt_type': 'credit_card', 'minimum_payment': '-1'},
    {'debt_type': 'auto_loan', 'payment_amount': '0', 'payment_frequency': 'monthly'},
    {'debt_type': 'auto_loan', 'payment_amount': '10'},
    {'debt_type': 'auto_loan', 'payment_frequency': 'monthly'},
    {'debt_type': 'auto_loan', 'payment_amount': '10', 'payment_frequency': 'daily'},
    {'debt_type': 'student_loan', 'credit_limit': '100'},
    {'debt_type': 'credit_card', 'payment_amount': '10', 'payment_frequency': 'monthly'},
])
def test_invalid_metadata_does_not_create_or_change_debt(client, changes):
    assert client.post('/api/debts', json={'name': 'Invalid', 'amount': '100', **changes}).status_code == 422
    debt = client.post('/api/debts', json={'name': 'Original', 'amount': '100'}).json()
    assert debt['debt_type'] == 'personal_debt'
    assert client.put(f"/api/debts/{debt['id']}", json={'name': 'Invalid', 'amount': '100', **changes}).status_code == 422
    assert client.get('/api/debts').json() == [debt]


def test_change_type_and_keep_history(client):
    debt = client.post('/api/debts', json={'name': 'Card', 'amount': '100', 'debt_type': 'credit_card', 'credit_limit': '50', 'minimum_payment': '10'}).json()
    # Over-limit debt is valid: do not prevent users recording their actual position.
    url = f"/api/debts/{debt['id']}"
    paid = client.post(url + '/payments', json={'amount': '10', 'paid_on': str(date.today())}).json()
    changed = client.put(url, json={'name': 'Loan', 'amount': '100', 'debt_type': 'personal_loan',
                                  'credit_limit': None, 'minimum_payment': None,
                                  'payment_amount': '10', 'payment_frequency': 'monthly'})
    assert changed.status_code == 200
    assert changed.json()['remaining_amount'] == '90.00'
    assert changed.json()['payments'] == paid['payments']
    assert changed.json()['credit_limit'] is None


def test_existing_sqlite_debt_upgrades_without_balance_changes(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE debts (id INTEGER PRIMARY KEY, name VARCHAR(120), amount NUMERIC, current_amount NUMERIC, due_date DATE, interest_rate NUMERIC, description TEXT, user_id CHAR(32))'))
        connection.execute(text("INSERT INTO debts (id, name, amount, current_amount, user_id) VALUES (1, 'Legacy', 100, 20, '00000000000040008000000000000001')"))
    initialize_database(engine)
    initialize_database(engine)  # Additive upgrade is repeatable.
    with engine.connect() as connection:
        row = connection.execute(text('SELECT * FROM debts')).mappings().one()
        assert row['debt_type'] == 'personal_debt'
        assert row['amount'] == 100
        assert row['current_amount'] == 20
        assert row['credit_limit'] is None
        assert row['payment_frequency'] is None
    engine.dispose()


def test_alembic_debt_upgrade_preserves_existing_data(tmp_path):
    path = Path(__file__).parents[1] / 'migrations/versions/20261102_01_debt_types.py'
    spec = importlib.util.spec_from_file_location('debt_type_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE debts (id INTEGER PRIMARY KEY, amount NUMERIC, current_amount NUMERIC)'))
        connection.execute(text('INSERT INTO debts VALUES (1, 100, 20)'))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        row = connection.execute(text('SELECT * FROM debts')).mappings().one()
        assert row['debt_type'] == 'personal_debt'
        assert row['amount'] - row['current_amount'] == 80
        assert row['payment_amount'] is None
        assert row['credit_limit'] is None
    engine.dispose()
