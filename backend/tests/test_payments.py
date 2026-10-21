from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import main
from app.database import Base
from app.models import Payment
from app.startup import initialize_database


def test_unified_ledger_dates_snapshots_filters_and_pagination(client):
    goal = client.post('/api/goals', json={'name': 'Trip', 'target_amount': '500', 'current_amount': '10'}).json()
    debt = client.post('/api/debts', json={'name': 'Loan', 'amount': '200', 'current_amount': '20'}).json()
    bill = client.post('/api/bills', json={'name': 'Rent', 'amount': '100', 'due_date': '2025-01-02'}).json()
    assert client.get('/api/payments').json()['total'] == 0  # Opening balances are not payments.
    assert client.post(f"/api/bills/{bill['id']}/payments", json={'amount': '100.01', 'paid_on': '2025-01-02'}).status_code == 201
    assert client.post(f"/api/debts/{debt['id']}/payments", json={'amount': '10.02', 'paid_on': '2025-01-02'}).status_code == 201
    assert client.post(f"/api/goals/{goal['id']}/contributions", json={'amount': '0.03'}).status_code == 200
    records = client.get('/api/payments').json()
    assert records['total'] == 3
    assert [row['kind'] for row in records['items']] == ['goal', 'debt', 'bill']
    assert records['items'][0]['amount'] == '0.03'
    assert records['items'][0]['paid_on'] == str(date.today())
    assert all(row['recorded_at'] for row in records['items'])
    assert all(row['recorded_at'].endswith('+00:00') for row in records['items'])
    assert records['items'][2]['due_date'] == '2025-01-02'
    client.put(f"/api/debts/{debt['id']}", json={'name': 'Renamed loan', 'amount': '200'})
    assert client.get('/api/payments?kind=debt').json()['items'][0]['target_name'] == 'Loan'
    page = client.get('/api/payments?page=2&page_size=2').json()
    assert page['total'] == 3 and page['pages'] == 2 and len(page['items']) == 1
    assert page['items'][0]['kind'] == 'bill'
    assert client.get('/api/payments?page=100&page_size=2').json()['page'] == 2


@pytest.mark.parametrize('query', ['kind=account', 'page=0', 'page=-1', 'page_size=0', 'page_size=101', 'page=1000001'])
def test_history_rejects_invalid_queries(client, query):
    assert client.get(f'/api/payments?{query}').status_code == 422


def test_empty_history(client):
    assert client.get('/api/payments?kind=goal&page=99').json() == {
        'items': [], 'total': 0, 'page': 1, 'page_size': 20, 'pages': 1,
    }


def test_account_backed_contributions_record_once_and_rejected_additions_do_not(client):
    account = client.post('/api/accounts', json={'name': 'Savings', 'account_type': 'Savings', 'balance': '10'}).json()
    goal = client.post('/api/goals', json={'name': 'Trip', 'target_amount': '100', 'account_id': account['id']}).json()
    assert client.post(f"/api/goals/{goal['id']}/contributions", json={'amount': '11'}).status_code == 422
    assert client.get('/api/payments').json()['total'] == 0
    assert client.post(f"/api/goals/{goal['id']}/contributions", json={'amount': '10'}).status_code == 200
    assert client.get('/api/accounts').json()[0]['balance'] == '10.00'
    pay = client.post('/api/paycheques', json={'amount': '10', 'allocations': [
        {'kind': 'goal', 'target_id': goal['id'], 'amount': '5'},
        {'kind': 'account', 'target_id': account['id'], 'amount': '5'},
    ]}).json()
    for allocation in pay['allocations']:
        assert client.post(f"/api/paycheques/{pay['id']}/allocations/{allocation['id']}/complete",
                           json={'completed_on': str(date.today())}).status_code == 200
    assert client.get('/api/accounts').json()[0]['balance'] == '20.00'
    assert client.get('/api/goals').json()[0]['current_amount'] == '15.00'
    assert client.get('/api/payments').json()['total'] == 2


def test_contributions_are_atomic_and_concurrent(client):
    goal = client.post('/api/goals', json={'name': 'Trip', 'target_amount': '100'}).json()
    url = f"/api/goals/{goal['id']}/contributions"
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: client.post(url, json={'amount': '0.01'}).status_code, range(8)))
    assert results == [200] * 8
    assert client.get('/api/goals').json()[0]['current_amount'] == '0.08'
    assert client.get('/api/payments').json()['total'] == 8


def test_failed_ledger_insert_rolls_back_balance(client, monkeypatch):
    from app.services import debts
    debt = client.post('/api/debts', json={'name': 'Loan', 'amount': '10'}).json()

    def fail(*args, **kwargs):
        raise RuntimeError('Simulated ledger write failure')

    monkeypatch.setattr(debts, 'add_payment', fail)
    with pytest.raises(RuntimeError, match='Simulated'):
        client.post(f"/api/debts/{debt['id']}/payments", json={'amount': '5', 'paid_on': str(date.today())})
    assert client.get('/api/debts').json()[0]['current_amount'] == '0.00'
    assert client.get('/api/payments').json()['total'] == 0


def test_completed_allocations_record_once_and_survive_plan_and_target_deletion(client):
    goal = client.post('/api/goals', json={'name': 'Trip', 'target_amount': '100'}).json()
    debt = client.post('/api/debts', json={'name': 'Loan', 'amount': '10'}).json()
    pay = client.post('/api/paycheques', json={'amount': '30', 'allocations': [
        {'kind': 'goal', 'target_id': goal['id'], 'amount': '20'},
        {'kind': 'debt', 'target_id': debt['id'], 'amount': '10'},
    ]}).json()
    assert client.get('/api/payments').json()['total'] == 0
    for allocation in pay['allocations']:
        url = f"/api/paycheques/{pay['id']}/allocations/{allocation['id']}/complete"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: client.post(url, json={'completed_on': str(date.today())}).status_code, range(2)))
        assert results == [200, 200]
    before = client.get('/api/payments').json()['items']
    assert len(before) == 2 and all(item['source'] == 'paycheque' for item in before)
    assert client.delete(f"/api/paycheques/{pay['id']}").status_code == 204
    assert client.delete(f"/api/goals/{goal['id']}").status_code == 204
    assert client.delete(f"/api/debts/{debt['id']}?resolve=true").status_code == 204
    after = client.get('/api/payments').json()['items']
    assert [item['target_name'] for item in after] == [item['target_name'] for item in before]
    assert all(item['target_id'] is None for item in after)
    # Reused SQLite IDs must not attach old payments to new targets/allocations.
    new_goal = client.post('/api/goals', json={'name': 'New goal', 'target_amount': '100'}).json()
    new_pay = client.post('/api/paycheques', json={'amount': '1', 'allocations': [
        {'kind': 'goal', 'target_id': new_goal['id'], 'amount': '1'},
    ]}).json()
    assert client.post(f"/api/paycheques/{new_pay['id']}/allocations/{new_pay['allocations'][0]['id']}/complete",
                       json={'completed_on': str(date.today())}).status_code == 200
    assert client.get('/api/payments').json()['total'] == 3


def legacy_database(tmp_path, amount='12.34'):
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO bills (id,name,amount,recurring,is_paid) VALUES (1,'Phone',20,0,1)"))
        connection.execute(text("INSERT INTO debts (id,name,amount,current_amount) VALUES (1,'Loan',100,12.34)"))
        connection.execute(text("INSERT INTO financial_goals (id,name,target_amount,current_amount) VALUES (1,'Trip',100,5.67)"))
        for kind in ['bill', 'debt']:
            connection.execute(text(f'CREATE TABLE {kind}_payments (id INTEGER PRIMARY KEY, {kind}_id INTEGER, amount NUMERIC(14,2), paid_on DATE, due_date DATE)'))
            connection.execute(text(f"INSERT INTO {kind}_payments VALUES (1,1,:amount,'2025-01-02','2025-01-01')"), {'amount': amount})
        connection.execute(text('INSERT INTO paycheques (id,amount) VALUES (1,20)'))
        for allocation_id, kind, cents in [(1, 'goal', 567), (2, 'debt', 1234)]:
            connection.execute(text(f"INSERT INTO paycheque_allocations (id,paycheque_id,{kind}_id,kind,name,amount_cents,status,completed_on) VALUES (:id,1,1,:kind,'Saved name',:cents,'completed','2025-01-02')"),
                               {'id': allocation_id, 'kind': kind, 'cents': cents})
    return engine


def test_migration_preserves_history_exact_amounts_and_balances_once(tmp_path):
    engine = legacy_database(tmp_path)
    try:
        for _ in range(2):
            initialize_database(engine)
        assert 'bill_payments' not in inspect(engine).get_table_names()
        assert 'debt_payments' not in inspect(engine).get_table_names()
        with Session(engine) as session:
            rows = session.scalars(select(Payment).order_by(Payment.id)).all()
            assert [(row.kind, row.amount) for row in rows] == [('bill', Decimal('12.34')), ('debt', Decimal('12.34')), ('goal', Decimal('5.67'))]
            assert all(row.recorded_at is None for row in rows)
            assert rows[2].target_name == 'Saved name' and rows[2].allocation_id == 1
            assert session.scalar(text('SELECT current_amount FROM financial_goals')) == 5.67
            assert session.scalar(text('SELECT current_amount FROM debts')) == 12.34
    finally:
        engine.dispose()


def test_migration_failure_preserves_legacy_tables_and_can_be_retried(tmp_path):
    engine = legacy_database(tmp_path, amount='0')
    try:
        with pytest.raises(IntegrityError):
            initialize_database(engine)
        assert {'bill_payments', 'debt_payments'} <= set(inspect(engine).get_table_names())
        with engine.begin() as connection:
            assert connection.scalar(text('SELECT COUNT(*) FROM payments')) == 0
            connection.execute(text('UPDATE bill_payments SET amount=12.34'))
            connection.execute(text('UPDATE debt_payments SET amount=12.34'))
        initialize_database(engine)
        with engine.connect() as connection:
            assert connection.scalar(text('SELECT COUNT(*) FROM payments')) == 3
    finally:
        engine.dispose()


@pytest.mark.parametrize('changes', [{'amount': Decimal('0')}, {'kind': 'account'}, {'debt_id': 123}, {'bill_id': 123}, {'source': 'planned'}])
def test_database_enforces_ledger_invariants(client, changes):
    with Session(main.engine) as session:
        session.add(Payment(**dict({'kind': 'goal', 'target_name': 'Trip', 'amount': Decimal('1'),
                                    'paid_on': date.today(), 'source': 'manual'}, **changes)))
        with pytest.raises(IntegrityError):
            session.commit()
