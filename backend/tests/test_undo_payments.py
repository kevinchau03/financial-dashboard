from conftest import TEST_USER_ID
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app import main
from app.models import Payment
from app.services import payments
from app.startup import initialize_database


def history(client):
    return client.get('/api/payments').json()['items']


def account(client, name='Savings', balance='100'):
    return client.post('/api/accounts', json={'name': name, 'account_type': 'Savings', 'balance': balance}).json()


def goal(client, account_id=None, name='Trip', current='0'):
    return client.post('/api/goals', json={'name': name, 'target_amount': '1000', 'account_id': account_id, 'current_amount': current}).json()


def complete(client, item, kind='goal', amount='25'):
    pay = client.post('/api/paycheques', json={'amount': amount, 'allocations': [
        {'kind': kind, 'target_id': item['id'], 'amount': amount},
    ]}).json()
    url = f"/api/paycheques/{pay['id']}/allocations/{pay['allocations'][0]['id']}/complete"
    assert client.post(url, json={'completed_on': str(date.today())}).status_code == 200
    return pay, url


def test_undo_debt_payment_reverses_balance_and_is_concurrently_idempotent(client):
    debt = client.post('/api/debts', json={'name': 'Loan', 'amount': '100', 'current_amount': '10'}).json()
    assert client.post(f"/api/debts/{debt['id']}/payments", json={'amount': '0.03', 'paid_on': '2025-01-01'}).status_code == 201
    payment_id = history(client)[0]['id']
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.delete(f'/api/payments/{payment_id}').status_code, range(2)))
    assert results == [204, 204]
    saved = client.get('/api/debts').json()[0]
    assert saved['current_amount'] == '10.00'
    assert saved['payments'] == []
    assert history(client) == []
    assert client.delete('/api/payments/999999').status_code == 404
    with Session(main.engine) as session:
        assert session.get(Payment, payment_id).undone_at is not None


@pytest.mark.parametrize('linked', [False, True])
def test_undo_direct_goal_contribution_keeps_account_balance(client, linked):
    a = account(client)
    g = goal(client, a['id'] if linked else None, current='5')
    client.post(f"/api/goals/{g['id']}/contributions", json={'amount': '0.10'})
    assert client.delete(f"/api/payments/{history(client)[0]['id']}").status_code == 204
    assert client.get('/api/goals').json()[0]['current_amount'] == '5.00'
    assert client.get('/api/accounts').json()[0]['balance'] == '100.00'


@pytest.mark.parametrize('kind', ['goal', 'debt'])
def test_undo_allocation_releases_amount_and_prevents_stale_completion(client, kind):
    item = goal(client) if kind == 'goal' else client.post('/api/debts', json={'name': 'Loan', 'amount': '100'}).json()
    pay, url = complete(client, item, kind)
    assert client.delete(f"/api/payments/{history(client)[0]['id']}").status_code == 204
    updated = client.get(f"/api/paycheques/{pay['id']}").json()
    assert updated['remaining_amount'] == '25.00'
    assert updated['allocations'][0]['status'] == 'cancelled'
    assert updated['allocations'][0]['completed_on'] is None
    assert client.post(url, json={'completed_on': str(date.today())}).status_code == 409
    assert client.get('/api/goals' if kind == 'goal' else '/api/debts').json()[0]['current_amount'] == '0.00'


def test_undo_goal_deposit_after_plan_deleted(client):
    a = account(client)
    g = goal(client, a['id'])
    pay, _ = complete(client, g)
    payment_id = history(client)[0]['id']
    assert client.delete(f"/api/paycheques/{pay['id']}").status_code == 204
    assert client.delete(f'/api/payments/{payment_id}').status_code == 204
    assert client.get('/api/accounts').json()[0]['balance'] == '100.00'
    assert client.get('/api/goals').json()[0]['current_amount'] == '0.00'


def test_undo_uses_original_deposit_account_and_rolls_back_if_earmarked(client):
    a, b = account(client, 'Original'), account(client, 'New')
    g = goal(client, a['id'])
    pay, _ = complete(client, g, amount='50')
    payment_id = history(client)[0]['id']
    assert client.put(f"/api/goals/{g['id']}", json={'name': 'Moved', 'target_amount': '1000', 'account_id': b['id']}).status_code == 200
    other = goal(client, a['id'], name='Other earmark', current='150')
    response = client.delete(f'/api/payments/{payment_id}')
    assert response.status_code == 409
    assert 'no longer available' in response.json()['detail']
    assert next(item for item in client.get('/api/goals').json() if item['id'] == g['id'])['current_amount'] == '50.00'
    assert client.get(f"/api/paycheques/{pay['id']}").json()['allocations'][0]['status'] == 'completed'
    assert len(history(client)) == 1
    assert client.delete(f"/api/goals/{other['id']}").status_code == 204
    assert client.delete(f'/api/payments/{payment_id}').status_code == 204
    assert {item['name']: item['balance'] for item in client.get('/api/accounts').json()} == {'Original': '100.00', 'New': '100.00'}


def test_new_account_link_does_not_invent_a_deposit_to_reverse(client):
    g = goal(client)
    complete(client, g)
    a = account(client)
    client.put(f"/api/goals/{g['id']}", json={'name': 'Trip', 'target_amount': '1000', 'account_id': a['id']})
    assert client.delete(f"/api/payments/{history(client)[0]['id']}").status_code == 204
    assert client.get('/api/accounts').json()[0]['balance'] == '100.00'


def test_undo_recurring_bill_in_record_order_restores_month_end_and_override(client):
    bill = client.post('/api/bills', json={'name': 'Internet', 'amount': '20', 'due_date': '2025-01-31', 'recurring': True}).json()
    url = f"/api/bills/{bill['id']}/payments"
    client.post(url, json={'amount': '20', 'paid_on': '2025-01-31'})
    first = history(client)[0]['id']
    # Deliberately backdated: undo order is recording order, not payment date.
    client.post(url, json={'amount': '20', 'paid_on': '2025-01-01', 'next_due_date': '2025-03-15'})
    second = next(p['id'] for p in history(client) if p['id'] != first)
    assert client.delete(f'/api/payments/{first}').status_code == 409
    assert client.delete(f'/api/payments/{second}').status_code == 204
    assert client.get('/api/bills').json()[0]['due_date'] == '2025-02-28'
    assert client.delete(f'/api/payments/{first}').status_code == 204
    saved = client.get('/api/bills').json()[0]
    assert saved['due_date'] == '2025-01-31' and saved['is_paid'] is False and saved['payments'] == []
    client.post(url, json={'amount': '20', 'paid_on': '2025-01-31'})
    client.post(url, json={'amount': '20', 'paid_on': '2025-02-28'})
    assert client.get('/api/bills').json()[0]['due_date'] == '2025-03-31'


def test_undo_one_time_bill_and_preserve_later_schedule_edits(client):
    bill = client.post('/api/bills', json={'name': 'Repair', 'amount': '20'}).json()
    url = f"/api/bills/{bill['id']}"
    client.post(url + '/payments', json={'amount': '20', 'paid_on': '2025-01-01'})
    first = history(client)[0]['id']
    assert client.delete(f'/api/payments/{first}').status_code == 204
    assert client.get('/api/bills').json()[0]['is_paid'] is False
    client.post(url + '/payments', json={'amount': '20', 'paid_on': '2025-01-01'})
    second = history(client)[0]['id']
    assert second != first  # Tombstones prevent ID reuse after deletion.
    client.put(url, json={'name': 'Repair', 'amount': '20', 'due_date': '2027-01-01'})
    assert client.delete(f'/api/payments/{second}').status_code == 409
    assert client.get('/api/bills').json()[0]['due_date'] == '2027-01-01'
    assert len(history(client)) == 1


def test_cannot_undo_deleted_target_or_unknown_legacy_side_effects(client):
    g = goal(client)
    client.post(f"/api/goals/{g['id']}/contributions", json={'amount': '5'})
    payment_id = history(client)[0]['id']
    client.delete(f"/api/goals/{g['id']}")
    assert client.delete(f'/api/payments/{payment_id}').status_code == 409
    assert history(client)[0]['undo_unavailable_reason']
    g = goal(client)
    complete(client, g)
    payment_id = history(client)[0]['id']
    with Session(main.engine) as session:
        payment = session.get(Payment, payment_id)
        payment.undo_state = None  # Existing paycheque contribution before snapshots.
        session.commit()
    assert client.delete(f'/api/payments/{payment_id}').status_code == 409
    assert client.get('/api/goals').json()[0]['current_amount'] == '25.00'


def test_undo_rolls_back_if_commit_fails(client, monkeypatch):
    g = goal(client)
    client.post(f"/api/goals/{g['id']}/contributions", json={'amount': '10'})
    payment_id = history(client)[0]['id']
    with Session(main.engine) as session:
        monkeypatch.setattr(session, 'commit', lambda: (_ for _ in ()).throw(RuntimeError('Commit failed')))
        with pytest.raises(RuntimeError, match='Commit failed'):
            payments.delete_payment(payment_id, session)
    assert client.get('/api/goals').json()[0]['current_amount'] == '10.00'
    assert len(history(client)) == 1


def test_history_clamps_after_undo_last_row_on_last_page(client):
    g = goal(client)
    for _ in range(21):
        client.post(f"/api/goals/{g['id']}/contributions", json={'amount': '1'})
    last = client.get('/api/payments?page=2').json()['items'][0]['id']
    assert client.delete(f'/api/payments/{last}').status_code == 204
    data = client.get('/api/payments?page=2').json()
    assert data['page'] == 1 and data['total'] == 20


def test_additive_upgrade_preserves_old_payment_rows_without_inventing_snapshots(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'old.db').as_posix()}")
    try:
        initialize_database(engine, legacy_owner=TEST_USER_ID)
        with engine.begin() as connection:
            connection.execute(text('DROP TABLE payments'))
            connection.execute(text('CREATE TABLE payments (id INTEGER PRIMARY KEY, kind VARCHAR(8), target_name VARCHAR(120), bill_id INTEGER, debt_id INTEGER, goal_id INTEGER, amount NUMERIC(14,2), paid_on DATE, due_date DATE, source VARCHAR(12), allocation_id INTEGER, recorded_at DATETIME)'))
            connection.execute(text("INSERT INTO payments (id,kind,target_name,amount,paid_on,source) VALUES (1,'debt','Loan',10,'2025-01-01','legacy')"))
        initialize_database(engine, legacy_owner=TEST_USER_ID)
        initialize_database(engine, legacy_owner=TEST_USER_ID)
        with engine.connect() as connection:
            assert connection.execute(text('SELECT target_name,amount,undo_state,undo_account_id,undone_at FROM payments')).one() == ('Loan', 10, None, None, None)
    finally:
        engine.dispose()
