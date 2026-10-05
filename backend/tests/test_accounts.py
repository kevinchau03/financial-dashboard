import pytest
from test_goals import client


def test_account_create_update_and_isolation(client):
    assert client.get('/api/accounts').json() == []
    payload = {'name': '  Savings  ', 'account_type': 'TFSA', 'balance': '1234.56'}
    response = client.post('/api/accounts', json=payload)
    assert response.status_code == 201
    saved = response.json()
    assert saved['name'] == 'Savings'
    assert saved['balance'] == '1234.56'
    assert client.get('/api/accounts').json() == [saved]
    updated = client.put(f"/api/accounts/{saved['id']}", json={**payload, 'balance': '-10.25'}).json()
    assert updated['balance'] == '-10.25'
    assert client.get('/api/accounts').json() == [updated]
    assert client.get('/api/analytics/savings').json() == {'total_savings': '0.00'}
    assert client.get('/api/goals').json() == []
    assert client.put('/api/accounts/9999', json=payload).status_code == 404


@pytest.mark.parametrize('change', [{'name': ' '}, {'account_type': 'unknown'}, {'balance': 'NaN'}, {'balance': '0.001'}, {'balance': '1000000000000'}])
def test_invalid_account(client, change):
    assert client.post('/api/accounts', json={'name': 'Account', 'account_type': 'Savings', 'balance': '0', **change}).status_code == 422
    assert client.get('/api/accounts').json() == []
