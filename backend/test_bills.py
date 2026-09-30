from test_goals import client  # noqa: F401 -- reuse the isolated database fixture


def test_create_and_list_bills(client):
    assert client.get('/api/bills').status_code == 200
    assert client.get('/api/bills').json() == []
    payload = {
        'name': 'Internet',
        'amount': '65.25',
        'due_date': '2026-10-15',
        'recurring': True,
        'description': 'Monthly internet bill',
    }
    response = client.post('/api/bills', json=payload)
    assert response.status_code == 201
    saved = response.json()
    assert saved == {**payload, 'id': saved['id'], 'is_paid': False, 'payments': []}

    assert client.get('/api/bills').json() == [saved]

    response = client.post('/api/bills', json={'name': 'Repair', 'amount': '20.00'})
    assert response.status_code == 201
    assert response.json()['recurring'] is False
    assert response.json()['due_date'] is None
    assert response.json()['description'] is None
    assert client.get('/api/bills').json() == [response.json(), saved]
