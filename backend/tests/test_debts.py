from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import main


def test_debt_payment_history_and_edit(client):
    assert client.get('/api/debts').json() == []
    response = client.post('/api/debts', json={
        'name': ' Loan ', 'amount': '100.30', 'current_amount': '10.10',
        'due_date': '2027-01-01', 'interest_rate': '4.25', 'description': 'Study',
    })
    assert response.status_code == 201
    debt = response.json()
    assert debt['name'] == 'Loan'
    assert debt['remaining_amount'] == '90.20'
    assert debt['payments'] == []
    url = f"/api/debts/{debt['id']}"
    first = client.post(url + '/payments', json={'amount': '20.20', 'paid_on': '2025-02-01'})
    assert first.status_code == 201
    assert first.json()['current_amount'] == '30.30'
    assert first.json()['remaining_amount'] == '70.00'
    assert first.json()['payments'][0]['due_date'] == '2027-01-01'
    # Editing never rewrites the paid balance or previous payment records.
    edited = client.put(url, json={'name': 'New loan', 'amount': '110.30'}).json()
    assert edited['remaining_amount'] == '80.00'
    assert edited['due_date'] is None
    assert edited['interest_rate'] is None
    assert edited['payments'] == first.json()['payments']
    assert client.put(url, json={'name': 'Invalid', 'amount': '20'}).status_code == 422
    assert client.put(url, json={'name': 'Invalid', 'amount': '100', 'current_amount': '0'}).status_code == 422
    final = client.post(url + '/payments', json={'amount': '80', 'paid_on': '2025-01-01'}).json()
    assert final['remaining_amount'] == '0.00'
    assert len(final['payments']) == 2
    assert final['payments'][0]['paid_on'] == '2025-02-01'
    assert client.post(url + '/payments', json={'amount': '0.01', 'paid_on': '2025-01-01'}).status_code == 422
    with TestClient(main.app) as restarted:
        assert restarted.get('/api/debts').json() == [final]


@pytest.mark.parametrize('changes', [
    {'name': ' '}, {'amount': '0'}, {'amount': '-1'}, {'amount': '1.001'},
    {'current_amount': '-1'}, {'current_amount': '101'},
    {'interest_rate': '-1'}, {'interest_rate': '100.01'}, {'interest_rate': '1.001'},
    {'due_date': '2026-02-30'},
])
def test_invalid_debt(client, changes):
    assert client.post('/api/debts', json={'name': 'Loan', 'amount': '100', **changes}).status_code == 422
    assert client.get('/api/debts').json() == []


@pytest.mark.parametrize('changes', [
    {'amount': '0'}, {'amount': '-1'}, {'amount': '0.001'}, {'amount': '100.01'},
    {'paid_on': (date.today() + timedelta(days=1)).isoformat()},
])
def test_invalid_payment_leaves_balance_and_history_unchanged(client, changes):
    debt = client.post('/api/debts', json={'name': 'Loan', 'amount': '100'}).json()
    response = client.post(f"/api/debts/{debt['id']}/payments", json={'amount': '20', 'paid_on': '2025-01-01', **changes})
    assert response.status_code == 422
    assert client.get('/api/debts').json() == [debt]


def test_decimal_final_payment_and_missing_debt(client):
    debt = client.post('/api/debts', json={'name': 'Small', 'amount': '0.30', 'current_amount': '0.10'}).json()
    result = client.post(f"/api/debts/{debt['id']}/payments", json={'amount': '0.20', 'paid_on': '2025-01-01'})
    assert result.status_code == 201
    assert result.json()['remaining_amount'] == '0.00'
    assert client.post('/api/debts/999/payments', json={'amount': '1', 'paid_on': '2025-01-01'}).status_code == 404
    assert client.put('/api/debts/999', json={'name': 'Missing', 'amount': '100'}).status_code == 404
