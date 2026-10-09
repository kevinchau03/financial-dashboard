from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, inspect
from app import main
from app.database import Base


def account(client, balance='100'):
    return client.post('/api/accounts', json={'name': 'Savings', 'account_type': 'Savings', 'balance': balance}).json()


def goal(client, account_id, value='40'):
    return client.post('/api/goals', json={'name': 'Car', 'target_amount': '1000', 'current_amount': value, 'account_id': account_id})


def test_earmarks_assignments_and_release(client):
    a = account(client)
    g = goal(client, a['id']).json()
    assert g['account_name'] == 'Savings'
    assert goal(client, a['id'], '70').status_code == 422
    assert client.post(f"/api/goals/{g['id']}/contributions", json={'amount': '20'}).status_code == 200
    saved = client.get('/api/accounts').json()[0]
    assert saved['balance'] == '100.00'
    assert saved['earmarked_amount'] == '60.00'
    assert saved['available_amount'] == '40.00'
    assert saved['goal_summary'][0]['id'] == g['id']
    assert client.post(f"/api/goals/{g['id']}/contributions", json={'amount': '41'}).status_code == 422
    assert client.put(f"/api/accounts/{a['id']}", json={'name': 'Savings', 'account_type': 'Savings', 'balance': '59'}).status_code == 422
    assert client.delete(f"/api/goals/{g['id']}").status_code == 204
    saved = client.get('/api/accounts').json()[0]
    assert saved['balance'] == '100.00'
    assert saved['available_amount'] == '100.00'


def test_relink_unlink_and_invalid_account(client):
    a = account(client)
    b = account(client, '10')
    g = goal(client, a['id']).json()
    payload = {'name': 'Car', 'target_amount': '1000', 'account_id': b['id']}
    assert client.put(f"/api/goals/{g['id']}", json=payload).status_code == 422
    assert client.get('/api/goals').json()[0]['account_id'] == a['id']
    assert client.put(f"/api/goals/{g['id']}", json={**payload, 'account_id': None}).status_code == 200
    assert goal(client, 999).status_code == 404
    assert client.get('/api/accounts').json()[1]['earmarked_amount'] == '0.00'


def test_paycheque_deposit_updates_linked_goal_once(client):
    a = account(client)
    g = goal(client, a['id']).json()
    pay = client.post('/api/paycheques', json={'amount': '25', 'allocations': [{'kind': 'goal', 'target_id': g['id'], 'amount': '25'}]}).json()
    assert client.get('/api/accounts').json()[0]['balance'] == '100.00'
    url = f"/api/paycheques/{pay['id']}/allocations/{pay['allocations'][0]['id']}/complete"
    for _ in range(2):
        assert client.post(url, json={'completed_on': date.today().isoformat()}).status_code == 200
    a = client.get('/api/accounts').json()[0]
    assert a['balance'] == '125.00'
    assert a['earmarked_amount'] == '65.00'
    assert a['available_amount'] == '60.00'


def test_existing_goal_schema_upgrade(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'old.db').as_posix()}", connect_args={'check_same_thread': False})
    with engine.begin() as c:
        c.execute(text('CREATE TABLE financial_goals (id INTEGER PRIMARY KEY, name VARCHAR(120), target_amount NUMERIC(14,2), current_amount NUMERIC(14,2), due_date DATE, description TEXT)'))
        c.execute(text("INSERT INTO financial_goals (id,name,target_amount,current_amount) VALUES (1,'Old',100,25)"))
    monkeypatch.setattr(main, 'engine', engine)
    try:
        with TestClient(main.app):
            assert 'account_id' in {col['name'] for col in inspect(engine).get_columns('financial_goals')}
            with engine.connect() as c:
                assert c.execute(text('SELECT name,current_amount,account_id FROM financial_goals')).one() == ('Old',25,None)
    finally:
        engine.dispose()
