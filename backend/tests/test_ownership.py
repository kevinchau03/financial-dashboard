from datetime import date
from uuid import UUID, uuid4
import pytest
from fastapi import HTTPException
from sqlalchemy import update, text
from app import main, database
from app.auth import get_current_user, AuthUser
from app.database import UserSession
from app.models import Account
from conftest import TEST_USER_ID

OTHER_USER = UUID('00000000-0000-4000-8000-000000000002')


def switch(user_id):
    main.app.dependency_overrides[get_current_user] = lambda: AuthUser(user_id, 'owner@example.test')


def test_lists_analytics_payments_and_references_are_private(client):
    account = client.post('/api/accounts', json={'name': 'Private account', 'account_type': 'Savings', 'balance': '100'}).json()
    goal = client.post('/api/goals', json={'name': 'Private goal', 'target_amount': '200', 'account_id': account['id']}).json()
    assert client.post(f"/api/goals/{goal['id']}/contributions", json={'amount': '20'}).status_code == 200
    payment = client.get('/api/payments').json()['items'][0]
    pay = client.post('/api/paycheques', json={'amount': '100', 'allocations': [{'kind': 'goal', 'target_id': goal['id'], 'amount': '10'}]}).json()
    switch(OTHER_USER)
    for path in ('accounts', 'goals', 'debts', 'bills', 'paycheques'):
        assert client.get(f'/api/{path}').json() == []
    assert client.get('/api/payments').json()['total'] == 0
    assert client.get('/api/analytics/savings').json()['total_savings'] == '0.00'
    assert client.get('/api/analytics/goals/contributions').json()['total_goal_contributions'] == '0.00'
    assert client.post(f"/api/goals/{goal['id']}/contributions", json={'amount': '1'}).status_code == 404
    assert client.delete(f"/api/payments/{payment['id']}").status_code == 404
    assert client.delete(f"/api/goals/{goal['id']}").status_code == 404
    assert client.post('/api/goals', json={'name': 'Cross-owner', 'target_amount': '100', 'account_id': account['id']}).status_code == 404
    assert client.put(f"/api/accounts/{account['id']}", json={'name': 'Stolen', 'account_type': 'Savings', 'balance': '100'}).status_code == 404
    assert client.get(f"/api/paycheques/{pay['id']}").status_code == 404
    allocation_id = pay['allocations'][0]['id']
    assert client.post(f"/api/paycheques/{pay['id']}/allocations/{allocation_id}/complete", json={'completed_on': str(date.today())}).status_code == 404
    assert client.post('/api/paycheques', json={'amount': '100', 'allocations': [{'kind': 'goal', 'target_id': goal['id'], 'amount': '10'}]}).status_code == 404
    switch(TEST_USER_ID)
    assert client.get('/api/analytics/savings').json()['total_savings'] == '20.00'
    assert client.get('/api/analytics/goals/contributions').json()['total_goal_contributions'] == '20.00'
    assert client.get('/api/payments').json()['total'] == 1
    assert client.get('/api/paycheques').json()[0]['allocations'][0]['status'] == 'planned'


def test_statement_downloads_and_duplicate_detection_are_per_user(client):
    def upload():
        response = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('private.csv', b'2026-01-01,Private transaction,10,,90')})
        assert response.status_code == 200
        return response.json()
    first = upload()
    assert upload()['already_imported'] is True
    switch(OTHER_USER)
    for suffix in ('', '/file', '/summary', '/insights'):
        assert client.get(f"/api/statements/{first['statement_id']}{suffix}").status_code == 404
    assert client.get('/api/statements').json()['total'] == 0
    second = upload()
    assert second['already_imported'] is False
    assert second['statement_id'] != first['statement_id']
    assert client.get('/api/statements').json()['total'] == 1
    assert client.get(f"/api/statements/{second['statement_id']}/file").status_code == 200


def test_retry_keys_are_scoped_to_the_owner(client):
    key = str(uuid4())
    first = client.post('/api/paycheques', json={'amount': '10', 'request_id': key}).json()
    switch(OTHER_USER)
    second = client.post('/api/paycheques', json={'amount': '25', 'request_id': key}).json()
    assert first['id'] != second['id']
    assert second['amount'] == '25.00'


def test_session_blocks_forged_owners_raw_sql_and_bulk_reassignment(client):
    with UserSession(database.engine, user_id=TEST_USER_ID) as session:
        session.add(Account(name='Wrong owner', account_type='Savings', balance=10, user_id=OTHER_USER))
        with pytest.raises(HTTPException):
            session.flush()
        session.rollback()
        with pytest.raises(RuntimeError, match='raw SQL'):
            session.execute(text('SELECT * FROM accounts'))
        with pytest.raises(RuntimeError, match='ownership'):
            session.execute(update(Account).values(user_id=OTHER_USER))
