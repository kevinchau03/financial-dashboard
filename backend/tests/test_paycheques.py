import pytest


def test_save_and_load_latest_paycheque(client):
    assert client.get('/api/paycheques/latest').json() is None
    first = client.post('/api/paycheques', json={'amount': '1250.25'})
    assert first.status_code == 201
    assert first.json()['amount'] == '1250.25'
    assert client.get('/api/paycheques/latest').json() == first.json()
    second = client.post('/api/paycheques', json={'amount': '1400'}).json()
    assert second['id'] != first.json()['id']
    assert client.get('/api/paycheques/latest').json() == second
    assert client.get('/api/analytics/savings').json() == {'total_savings': '0.00'}


@pytest.mark.parametrize('value', ['0', '-1', '1.001', 'NaN', '1000000000000'])
def test_invalid_paycheque(client, value):
    assert client.post('/api/paycheques', json={'amount': value}).status_code == 422
    assert client.get('/api/paycheques/latest').json() is None
