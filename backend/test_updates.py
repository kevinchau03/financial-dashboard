from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, inspect

import main
from test_goals import client


def test_edit_goal(client):
    goal = client.post('/api/goals', json={'name': 'Trip', 'target_amount': '100', 'current_amount': '210.15', 'due_date': '2027-01-01'}).json()
    payload = {'name': 'Holiday', 'target_amount': '200', 'due_date': None, 'description': 'Done'}
    response = client.put(f"/api/goals/{goal['id']}", json=payload)
    assert response.status_code == 200
    assert response.json()['current_amount'] == '210.15'
    assert response.json()['due_date'] is None
    assert client.get('/api/goals').json() == [response.json()]
    assert client.put(f"/api/goals/{goal['id']}", json={**payload, 'current_amount': '-1'}).status_code == 422
    assert client.put('/api/goals/999', json=payload).status_code == 404


def test_contributions_add_and_survive_editing(client):
    goal = client.post('/api/goals', json={'name': 'Trip', 'target_amount': '100', 'current_amount': '10.10'}).json()
    url = f"/api/goals/{goal['id']}"
    for addition, expected in [('0.20', '10.30'), ('100', '110.30')]:
        response = client.post(url + '/contributions', json={'amount': addition})
        assert response.status_code == 200
        assert response.json()['current_amount'] == expected
    edited = client.put(url, json={'name': 'Holiday', 'target_amount': '200'}).json()
    assert edited['current_amount'] == '110.30'
    assert client.get('/api/goals').json() == [edited]
    assert client.post('/api/goals/999/contributions', json={'amount': '1'}).status_code == 404


@pytest.mark.parametrize('amount', ['0', '-1', '0.001', 'NaN', '1000000000000'])
def test_invalid_contribution(client, amount):
    goal = client.post('/api/goals', json={'name': 'Trip', 'target_amount': '100'}).json()
    assert client.post(f"/api/goals/{goal['id']}/contributions", json={'amount': amount}).status_code == 422
    assert client.get('/api/goals').json()[0]['current_amount'] == '0.00'


def test_contribution_balance_limit(client):
    goal = client.post('/api/goals', json={'name': 'Trip', 'target_amount': '100', 'current_amount': '999999999999.98'}).json()
    url = f"/api/goals/{goal['id']}/contributions"
    assert client.post(url, json={'amount': '0.02'}).status_code == 422
    assert client.get('/api/goals').json()[0]['current_amount'] == '999999999999.98'
    assert client.post(url, json={'amount': '0.01'}).json()['current_amount'] == '999999999999.99'


def test_payment_and_next_occurrence(client):
    bill = client.post('/api/bills', json={'name': 'Internet', 'amount': '65', 'recurring': True, 'due_date': '2025-01-10'}).json()
    url = f"/api/bills/{bill['id']}"
    response = client.post(url + '/payments', json={'amount': '60.25', 'paid_on': '2025-01-10', 'next_due_date': '2025-02-10'})
    assert response.status_code == 201
    saved = response.json()
    assert saved['is_paid'] is False
    assert saved['due_date'] == '2025-02-10'
    assert saved['payments'][0]['due_date'] == '2025-01-10'
    assert saved['payments'][0]['amount'] == '60.25'
    second = client.post(url + '/payments', json={'amount': '65', 'paid_on': '2025-02-10'})
    assert second.status_code == 201
    assert second.json()['is_paid'] is True
    assert len(second.json()['payments']) == 2
    assert second.json()['payments'][0]['paid_on'] == '2025-02-10'
    assert client.post(url + '/payments', json={'amount': '65', 'paid_on': '2025-02-10'}).status_code == 409
    edited = client.put(url, json={'name': 'New internet', 'amount': '70', 'recurring': True, 'due_date': '2025-03-10'}).json()
    assert edited['is_paid'] is False
    assert len(edited['payments']) == 2
    assert client.get('/api/bills').json() == [edited]


@pytest.mark.parametrize('changes', [
    {'amount': '0'}, {'amount': '1.001'},
    {'paid_on': (date.today() + timedelta(days=1)).isoformat()},
    {'next_due_date': '2025-01-01'},
])
def test_invalid_payment(client, changes):
    bill = client.post('/api/bills', json={'name': 'Bill', 'amount': '20', 'recurring': True, 'due_date': '2025-01-10'}).json()
    response = client.post(f"/api/bills/{bill['id']}/payments", json={'amount': '20', 'paid_on': '2025-01-10', **changes})
    assert response.status_code == 422
    assert client.get('/api/bills').json()[0]['payments'] == []


def test_one_time_payment_and_edit(client):
    bill = client.post('/api/bills', json={'name': 'Repair', 'amount': '20'}).json()
    url = f"/api/bills/{bill['id']}"
    assert client.post(url + '/payments', json={'amount': '20', 'paid_on': '2025-01-01', 'next_due_date': '2025-02-01'}).status_code == 422
    assert client.post(url + '/payments', json={'amount': '20', 'paid_on': '2025-01-01'}).json()['is_paid'] is True
    assert client.put(url, json={'name': 'Repair updated', 'amount': '20'}).json()['is_paid'] is True
    assert client.put('/api/bills/999', json={'name': 'Missing', 'amount': '20'}).status_code == 404
    assert client.post('/api/bills/999/payments', json={'amount': '20', 'paid_on': '2025-01-01'}).status_code == 404


def test_existing_database_upgrade(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}", connect_args={'check_same_thread': False})
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE bills (id INTEGER PRIMARY KEY, name VARCHAR(120), amount NUMERIC(14,2), due_date DATE, recurring BOOLEAN, description TEXT)'))
        connection.execute(text("INSERT INTO bills VALUES (1, 'Existing', 25, NULL, 0, NULL)"))
    monkeypatch.setattr(main, 'engine', engine)
    for _ in range(2):
        with TestClient(main.app):
            pass
    assert 'bill_payments' in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.execute(text('SELECT name, is_paid FROM bills')).one() == ('Existing', 0)
    engine.dispose()
