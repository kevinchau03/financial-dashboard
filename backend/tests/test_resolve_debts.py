def test_resolve_requires_zero_balance(client):
    debt = client.post('/api/debts', json={'name': 'Loan', 'amount': '10'}).json()
    url = f"/api/debts/{debt['id']}?resolve=true"
    assert client.delete(url).status_code == 409
    assert len(client.get('/api/debts').json()) == 1
    from datetime import date
    assert client.post(f"/api/debts/{debt['id']}/payments", json={'amount': '10', 'paid_on': date.today().isoformat()}).status_code == 201
    assert client.delete(url).status_code == 204
    assert client.get('/api/debts').json() == []
    assert client.delete(url).status_code == 404
