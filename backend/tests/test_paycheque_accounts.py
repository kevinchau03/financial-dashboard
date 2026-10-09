from datetime import date
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app import main
from app.models import PaychequeAllocation, PaychequeAllocationBatch


def test_account_plan_completion_and_deletion(client):
    account = client.post('/api/accounts', json={'name': 'Car savings', 'account_type': 'Savings', 'balance': '50'}).json()
    goal = client.post('/api/goals', json={'name': 'Car', 'target_amount': '1000'}).json()
    debt = client.post('/api/debts', json={'name': 'Loan', 'amount': '100'}).json()
    pay = client.post('/api/paycheques', json={'amount': '100', 'allocations': [
        {'kind': 'account', 'target_id': account['id'], 'amount': '30.25'},
        {'kind': 'goal', 'target_id': goal['id'], 'amount': '10'},
        {'kind': 'debt', 'target_id': debt['id'], 'amount': '20'},
    ]}).json()
    assert client.get('/api/accounts').json()[0]['balance'] == '50.00'
    assert pay['allocated_amount'] == '60.25'
    for allocation in pay['allocations']:
        url = f"/api/paycheques/{pay['id']}/allocations/{allocation['id']}/complete"
        for _ in range(2):
            assert client.post(url, json={'completed_on': date.today().isoformat()}).status_code == 200
    assert client.get('/api/accounts').json()[0]['balance'] == '80.25'
    assert client.get('/api/goals').json()[0]['current_amount'] == '10.00'
    assert client.get('/api/debts').json()[0]['current_amount'] == '20.00'
    assert client.post(f"/api/paycheques/{pay['id']}/allocations", json={
        'request_id': str(uuid4()), 'allocations': [{'kind': 'account', 'target_id': account['id'], 'amount': '5'}],
    }).status_code == 200
    assert client.delete(f"/api/paycheques/{pay['id']}").status_code == 204
    assert client.get('/api/paycheques/latest').json() is None
    assert client.get('/api/paycheques').json() == []
    assert client.get('/api/accounts').json()[0]['balance'] == '80.25'
    assert client.get('/api/goals').json()[0]['current_amount'] == '10.00'
    assert len(client.get('/api/debts').json()[0]['payments']) == 1
    with Session(main.engine) as session:
        assert session.scalar(select(func.count()).select_from(PaychequeAllocation)) == 0
        assert session.scalar(select(func.count()).select_from(PaychequeAllocationBatch)) == 0
    assert client.delete(f"/api/paycheques/{pay['id']}").status_code == 404


def test_account_cancel_missing_target_and_overflow(client):
    assert client.post('/api/paycheques', json={'amount': '10', 'allocations': [
        {'kind': 'account', 'target_id': 999, 'amount': '5'},
    ]}).status_code == 404
    assert client.get('/api/paycheques').json() == []
    account = client.post('/api/accounts', json={'name': 'Full', 'account_type': 'TFSA', 'balance': '999999999999.99'}).json()
    pay = client.post('/api/paycheques', json={'amount': '10', 'allocations': [
        {'kind': 'account', 'target_id': account['id'], 'amount': '5'},
    ]}).json()
    allocation = pay['allocations'][0]
    base = f"/api/paycheques/{pay['id']}/allocations/{allocation['id']}"
    assert client.post(base + '/complete', json={'completed_on': date.today().isoformat()}).status_code == 422
    assert client.get(f"/api/paycheques/{pay['id']}").json()['allocations'][0]['status'] == 'planned'
    response = client.post(base + '/cancel')
    assert response.status_code == 200
    assert response.json()['remaining_amount'] == '10.00'


def test_upgrade_keeps_existing_allocations(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text, inspect
    from app.database import Base
    engine = create_engine(f"sqlite:///{(tmp_path / 'old.db').as_posix()}", connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine, tables=[table for table in Base.metadata.sorted_tables if table.name != 'paycheque_allocations'])
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE paycheque_allocations (id INTEGER PRIMARY KEY, paycheque_id INTEGER NOT NULL, goal_id INTEGER, debt_id INTEGER, kind VARCHAR(8) NOT NULL, name VARCHAR(120) NOT NULL, amount_cents INTEGER NOT NULL, status VARCHAR(12) NOT NULL, completed_on DATE)'))
        connection.execute(text("INSERT INTO paycheques (id, amount, allocated_cents) VALUES (1, 100, 2500)"))
        connection.execute(text("INSERT INTO paycheque_allocations (paycheque_id, kind, name, amount_cents, status) VALUES (1, 'goal', 'Old goal', 2500, 'planned')"))
    monkeypatch.setattr(main, 'engine', engine)
    try:
        with TestClient(main.app):
            assert 'account_id' in {column['name'] for column in inspect(engine).get_columns('paycheque_allocations')}
            with Session(engine) as session:
                allocation = session.scalar(select(PaychequeAllocation))
                assert allocation.name == 'Old goal'
                assert allocation.amount_cents == 2500
                assert allocation.account_id is None
    finally:
        engine.dispose()
