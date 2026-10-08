

def test_debt_and_bill_summaries(client):
    assert client.get('/api/analytics/debts').json() == {'total_debt': '0.00'}
    assert client.get('/api/analytics/bills').json() == {'total_bills': '0.00'}
    debt = client.post('/api/debts', json={'name': 'Loan', 'amount': '100.50', 'current_amount': '20.25'}).json()
    client.post('/api/goals', json={'name': 'Savings', 'target_amount': '1000', 'current_amount': '500'})
    assert client.get('/api/analytics/debts').json() == {'total_debt': '80.25'}
    client.post(f"/api/debts/{debt['id']}/payments", json={'amount': '10.25', 'paid_on': '2025-01-01'})
    assert client.get('/api/analytics/debts').json() == {'total_debt': '70.00'}
    bill = client.post('/api/bills', json={'name': 'Internet', 'amount': '40.10'}).json()
    client.post('/api/bills', json={'name': 'Gym', 'amount': '20.20'})
    assert client.get('/api/analytics/bills').json() == {'total_bills': '60.30'}
    client.post(f"/api/bills/{bill['id']}/payments", json={'amount': '40.10', 'paid_on': '2025-01-01'})
    assert client.get('/api/analytics/bills').json() == {'total_bills': '60.30'}
    client.put(f"/api/bills/{bill['id']}", json={'name': 'Internet', 'amount': '50.10'})
    assert client.get('/api/analytics/bills').json() == {'total_bills': '70.30'}


def test_total_savings_updates(client):
    response = client.get('/api/analytics/savings')
    assert response.status_code == 200
    assert response.json() == {'total_savings': '0.00'}
    first = client.post('/api/goals', json={
        'name': 'Trip', 'target_amount': '100', 'current_amount': '10.10',
    }).json()
    client.post('/api/goals', json={
        'name': 'Car', 'target_amount': '1000', 'current_amount': '20.20',
    })
    client.post('/api/debts', json={'name': 'Loan', 'amount': '100', 'current_amount': '50'})
    assert client.get('/api/analytics/savings').json() == {'total_savings': '30.30'}
    client.post(f"/api/goals/{first['id']}/contributions", json={'amount': '0.20'})
    assert client.get('/api/analytics/savings').json() == {'total_savings': '30.50'}
