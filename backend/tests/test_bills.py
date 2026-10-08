import pytest


@pytest.mark.parametrize('start,following,third', [
    ('2025-01-31', '2025-02-28', '2025-03-31'),
    ('2024-01-31', '2024-02-29', '2024-03-31'),
    ('2024-12-15', '2025-01-15', '2025-02-15'),
])
def test_monthly_payment_keeps_original_day(client, start, following, third):
    bill = client.post('/api/bills', json={'name': 'Monthly', 'amount': '10', 'recurring': True, 'due_date': start}).json()
    url = f"/api/bills/{bill['id']}/payments"
    for expected in (following, third):
        # Even a late payment advances one occurrence, without skipping debt.
        response = client.post(url, json={'amount': '10', 'paid_on': '2025-06-01'})
        assert response.status_code == 201
        assert response.json()['due_date'] == expected
        assert response.json()['is_paid'] is False
    assert {p['due_date'] for p in response.json()['payments']} == {start, following}


def test_monthly_requires_date(client):
    assert client.post('/api/bills', json={'name': 'Monthly', 'amount': '10', 'recurring': True}).status_code == 422


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
