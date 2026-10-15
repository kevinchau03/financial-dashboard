from uuid import uuid4


def test_saved_reserves_limit_allocations_and_do_not_change_balances(client):
    goal = client.post('/api/goals', json={'name': 'Car', 'target_amount': '1000', 'current_amount': '0'}).json()
    key = str(uuid4())
    payload = {'amount': '1000', 'bills_reserved': '300', 'spending_reserved': '200', 'request_id': key,
               'allocations': [{'kind': 'goal', 'target_id': goal['id'], 'amount': '400'}]}
    response = client.post('/api/paycheques', json=payload)
    assert response.status_code == 201
    pay = response.json()
    assert pay['remaining_amount'] == '100.00'
    assert pay['bills_reserved'] == '300.00'
    assert client.get('/api/goals').json()[0]['current_amount'] == '0.00'
    assert client.post('/api/paycheques', json=payload).json()['id'] == pay['id']
    payload['spending_reserved'] = '201'
    assert client.post('/api/paycheques', json=payload).status_code == 409
    assert client.post(f"/api/paycheques/{pay['id']}/allocations", json={'request_id': str(uuid4()), 'allocations': [{'kind': 'goal', 'target_id': goal['id'], 'amount': '101'}]}).status_code == 422
    allocation = pay['allocations'][0]['id']
    cancelled = client.post(f"/api/paycheques/{pay['id']}/allocations/{allocation}/cancel").json()
    assert cancelled['remaining_amount'] == '500.00'


def test_invalid_reserves_and_payday(client):
    for extra in [{'bills_reserved': '101'}, {'spending_reserved': '-1'}, {'bills_reserved': '0.001'}, {'received_on': '2026-01-02', 'next_payday': '2026-01-01'}]:
        assert client.post('/api/paycheques', json={'amount': '100', **extra}).status_code == 422
    assert client.get('/api/paycheques/latest').json() is None
