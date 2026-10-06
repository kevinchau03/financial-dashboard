from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from test_goals import client


def target(client, kind):
    payload = {'name': 'Vacation' if kind == 'goal' else 'Car loan',
               'target_amount' if kind == 'goal' else 'amount': '1000'}
    response = client.post('/api/goals' if kind == 'goal' else '/api/debts', json=payload)
    assert response.status_code == 201
    return response.json()


def plan(client, entries, amount='500'):
    response = client.post('/api/paycheques', json={
        'amount': amount, 'received_on': str(date.today()), 'request_id': str(uuid4()), 'allocations': entries,
    })
    assert response.status_code == 201, response.text
    return response.json()


def entry(kind, item, amount):
    return {'kind': kind, 'target_id': item['id'], 'amount': amount}


def action_url(pay, allocation, action):
    return f"/api/paycheques/{pay['id']}/allocations/{allocation['id']}/{action}"


def test_plan_then_record_savings_and_debt_payment(client):
    goal, debt = target(client, 'goal'), target(client, 'debt')
    pay = plan(client, [entry('goal', goal, '100.10'), entry('debt', debt, '200.20')])
    assert pay['allocated_amount'] == '300.30'
    assert pay['remaining_amount'] == '199.70'
    assert client.get('/api/analytics/savings').json()['total_savings'] == '0.00'
    assert client.get('/api/debts').json()[0]['payments'] == []
    for allocation in pay['allocations']:
        for _ in range(2):
            response = client.post(action_url(pay, allocation, 'complete'), json={'completed_on': str(date.today())})
            assert response.status_code == 200, response.text
    assert client.get('/api/goals').json()[0]['current_amount'] == '100.10'
    saved_debt = client.get('/api/debts').json()[0]
    assert saved_debt['current_amount'] == '200.20'
    assert len(saved_debt['payments']) == 1
    assert saved_debt['payments'][0]['amount'] == '200.20'
    assert client.get(f"/api/paycheques/{pay['id']}").json()['remaining_amount'] == '199.70'


def test_allocation_requests_are_atomic_and_retryable(client):
    goal = target(client, 'goal')
    payload = {'amount': '100', 'request_id': str(uuid4()), 'allocations': [entry('goal', goal, '60')]}
    first = client.post('/api/paycheques', json=payload).json()
    assert client.post('/api/paycheques', json=payload).json() == first
    assert client.post('/api/paycheques', json={**payload, 'amount': '101'}).status_code == 409
    batch = {'request_id': str(uuid4()), 'allocations': [entry('goal', goal, '40')]}
    url = f"/api/paycheques/{first['id']}/allocations"
    assert client.post(url, json=batch).status_code == 200
    assert client.post(url, json=batch).status_code == 200
    assert client.post(url, json={**batch, 'allocations': [entry('goal', goal, '1')]}).status_code == 409
    assert client.post(url, json={**batch, 'request_id': str(uuid4())}).status_code == 422
    saved = client.get(f"/api/paycheques/{first['id']}").json()
    assert saved['remaining_amount'] == '0.00'
    assert len(saved['allocations']) == 2
    invalid = client.post('/api/paycheques', json={'amount': '100', 'allocations': [entry('goal', goal, '101')]})
    assert invalid.status_code == 422
    assert len(client.get('/api/paycheques').json()) == 1


def test_cancel_releases_once_and_preserves_history(client):
    goal = target(client, 'goal')
    pay = plan(client, [entry('goal', goal, '100')])
    url = action_url(pay, pay['allocations'][0], 'cancel')
    for _ in range(2):
        response = client.post(url)
        assert response.status_code == 200
        assert response.json()['remaining_amount'] == '500.00'
    assert response.json()['allocations'][0]['status'] == 'cancelled'
    assert client.post(action_url(pay, pay['allocations'][0], 'complete'), json={'completed_on': str(date.today())}).status_code == 409


@pytest.mark.parametrize('kind', ['goal', 'debt'])
def test_deletion_releases_pending_and_retains_completed_history(client, kind):
    item = target(client, kind)
    pay = plan(client, [entry(kind, item, '100')])
    url = f"/api/paycheques/{pay['id']}/allocations"
    response = client.post(url, json={'request_id': str(uuid4()), 'allocations': [entry(kind, item, '50')]}).json()
    first = response['allocations'][0]
    assert client.post(action_url(pay, first, 'complete'), json={'completed_on': str(date.today())}).status_code == 200
    assert client.post(action_url(pay, first, 'cancel')).status_code == 409
    assert client.delete(f"/api/{'goals' if kind == 'goal' else 'debts'}/{item['id']}").status_code == 204
    saved = client.get(f"/api/paycheques/{pay['id']}").json()
    assert saved['remaining_amount'] == '400.00'
    assert [allocation['status'] for allocation in saved['allocations']] == ['completed', 'cancelled']
    assert all(allocation[f'{kind}_id'] is None for allocation in saved['allocations'])
    assert all(allocation['name'] == item['name'] for allocation in saved['allocations'])


def test_stale_debt_balance_and_other_reserved_paycheques(client):
    debt = target(client, 'debt')
    pay = plan(client, [entry('debt', debt, '900')], '1000')
    response = client.post('/api/paycheques', json={'amount': '200', 'allocations': [entry('debt', debt, '101')]})
    assert response.status_code == 422
    assert client.post(f"/api/debts/{debt['id']}/payments", json={'amount': '200', 'paid_on': str(date.today())}).status_code == 201
    assert client.post(action_url(pay, pay['allocations'][0], 'complete'), json={'completed_on': str(date.today())}).status_code == 422
    assert client.get(f"/api/paycheques/{pay['id']}").json()['allocations'][0]['status'] == 'planned'
    assert len(client.get('/api/debts').json()[0]['payments']) == 1


def test_dates_and_missing_targets_rollback(client):
    goal = target(client, 'goal')
    tomorrow = str(date.today() + timedelta(days=1))
    assert client.post('/api/paycheques', json={'amount': '100', 'received_on': tomorrow}).status_code == 422
    assert client.post('/api/paycheques', json={'amount': '100', 'allocations': [entry('goal', goal, '10'), {'kind': 'goal', 'target_id': 999, 'amount': '10'}]}).status_code == 404
    assert client.get('/api/paycheques').json() == []
    pay = plan(client, [entry('goal', goal, '.30')], '.30')
    for invalid in [tomorrow, str(date.today() - timedelta(days=1))]:
        assert client.post(action_url(pay, pay['allocations'][0], 'complete'), json={'completed_on': invalid}).status_code == 422
    assert pay['remaining_amount'] == '0.00'


def test_concurrent_reservation_and_completion(client):
    goal = target(client, 'goal')
    pay = plan(client, [], '100')
    def reserve(_):
        return client.post(f"/api/paycheques/{pay['id']}/allocations", json={'request_id': str(uuid4()), 'allocations': [entry('goal', goal, '60')]}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(reserve, range(2))) == [200, 422]
    saved = client.get(f"/api/paycheques/{pay['id']}").json()
    def complete(_):
        return client.post(action_url(saved, saved['allocations'][0], 'complete'), json={'completed_on': str(date.today())}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(complete, range(2))) == [200, 200]
    assert Decimal(client.get('/api/goals').json()[0]['current_amount']) == Decimal('60')


def test_legacy_paycheque_is_preserved_at_startup(client):
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    import main
    # Reconstruct the previous table only in this test's disposable database.
    with main.engine.begin() as connection:
        connection.execute(text('DROP TABLE paycheques'))
        connection.execute(text('CREATE TABLE paycheques (id INTEGER PRIMARY KEY, amount NUMERIC(14,2) NOT NULL)'))
        connection.execute(text('INSERT INTO paycheques (id, amount) VALUES (7, 75.25)'))
    with TestClient(main.app) as restarted:
        saved = restarted.get('/api/paycheques/latest').json()
        assert saved['id'] == 7
        assert saved['amount'] == '75.25'
        assert saved['received_on'] is None
        assert saved['remaining_amount'] == '75.25'
        assert saved['allocations'] == []
