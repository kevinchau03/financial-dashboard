"""Opt-in checks against the migrated project, entirely inside a rollback."""
import os
from datetime import date
from typing import Annotated
from uuid import uuid4
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from app import main
from app.auth import AuthUser, get_current_user
from app.database import build_engine, get_session, UserSession

pytestmark = pytest.mark.skipif(os.getenv('RUN_SUPABASE_TESTS') != '1', reason='Opt-in live Supabase checks')


@pytest.fixture
def project():
    engine = build_engine(os.getenv('MIGRATION_DATABASE_URL') or os.environ['DATABASE_URL'])
    assert engine.dialect.name == 'postgresql'
    first, second = uuid4(), uuid4()
    current = [first]
    with engine.connect() as connection:
        outer = connection.begin()
        try:
            # These Auth rows never commit and cannot sign in or receive email.
            for user_id in (first, second):
                connection.execute(text("INSERT INTO auth.users (id, aud, role) VALUES (:id, 'authenticated', 'authenticated')"), {'id': user_id})

            def scoped(user: Annotated[AuthUser, Depends(get_current_user)]):
                with UserSession(connection, user_id=user.id, join_transaction_mode='create_savepoint') as session:
                    yield session

            main.app.dependency_overrides[get_current_user] = lambda: AuthUser(current[0], 'integration@example.test')
            main.app.dependency_overrides[get_session] = scoped
            with TestClient(main.app) as client:
                yield client, connection, current, first, second
        finally:
            main.app.dependency_overrides.clear()
            outer.rollback()
    engine.dispose()


def test_postgres_financial_flow_and_owner_isolation(project):
    client, connection, current, first, second = project
    account_response = client.post('/api/accounts', json={'name': 'Integration account', 'account_type': 'Savings', 'balance': '100'})
    assert account_response.status_code == 201
    account = account_response.json()
    goal_response = client.post('/api/goals', json={'name': 'Integration goal', 'target_amount': '100', 'account_id': account['id']})
    assert goal_response.status_code == 201
    goal = goal_response.json()
    assert client.post(f"/api/goals/{goal['id']}/contributions", json={'amount': '20'}).status_code == 200
    payment = client.get('/api/payments').json()['items'][0]
    pay_response = client.post('/api/paycheques', json={'amount': '100', 'allocations': [{'kind': 'goal', 'target_id': goal['id'], 'amount': '10'}]})
    assert pay_response.status_code == 201
    pay = pay_response.json()
    assert client.post(f"/api/paycheques/{pay['id']}/allocations/{pay['allocations'][0]['id']}/complete", json={'completed_on': str(date.today())}).status_code == 200
    assert client.get('/api/accounts').json()[0]['balance'] == '110.00'
    allocation_payment = next(row for row in client.get('/api/payments').json()['items'] if row['source'] == 'paycheque')
    assert client.delete(f"/api/payments/{allocation_payment['id']}").status_code == 204
    assert client.get('/api/accounts').json()[0]['balance'] == '100.00'
    assert client.get('/api/analytics/goals/contributions').json()['total_goal_contributions'] == '20.00'

    def upload():
        response = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('integration.csv', b'2026-01-01,Test debit,10,,90')})
        assert response.status_code == 200
        return response.json()
    statement = upload()
    assert client.get('/api/statements').json()['total'] == 1
    assert client.get(f"/api/statements/{statement['statement_id']}/insights").status_code == 200
    current[0] = second
    assert client.get('/api/accounts').json() == []
    assert client.get('/api/payments').json()['total'] == 0
    assert client.get('/api/analytics/savings').json()['total_savings'] == '0.00'
    assert client.delete(f"/api/payments/{payment['id']}").status_code == 404
    assert client.get(f"/api/statements/{statement['statement_id']}/file").status_code == 404
    assert upload()['already_imported'] is False
    current[0] = first
    assert client.delete(f"/api/payments/{payment['id']}").status_code == 204
    assert client.get('/api/analytics/savings').json()['total_savings'] == '0.00'
    assert client.delete(f"/api/goals/{goal['id']}").status_code == 204


def test_database_itself_enforces_rls_links_and_permissions(project):
    client, connection, current, first, second = project
    account = client.post('/api/accounts', json={'name': 'Private', 'account_type': 'Savings', 'balance': '100'}).json()
    connection.execute(text("SELECT set_config('app.user_id', :id, true)"), {'id': str(second)})
    # Raw SQL deliberately bypasses every ORM filter to test actual RLS.
    assert connection.scalar(text('SELECT count(*) FROM accounts')) == 0
    assert connection.execute(text('UPDATE accounts SET balance = 0 WHERE id = :id'), {'id': account['id']}).rowcount == 0
    with pytest.raises(DBAPIError) as denied:
        with connection.begin_nested():
            connection.execute(text("INSERT INTO accounts (name, account_type, balance, user_id) VALUES ('Forged', 'Savings', 0, :id)"), {'id': first})
    assert denied.value.orig.sqlstate == '42501'
    with pytest.raises(DBAPIError) as cross_owner:
        with connection.begin_nested():
            connection.execute(text("INSERT INTO financial_goals (name, target_amount, current_amount, account_id, user_id) VALUES ('Forged reference', 10, 0, :account, :owner)"), {'account': account['id'], 'owner': second})
    assert cross_owner.value.orig.sqlstate == '23503'
    connection.execute(text("SELECT set_config('app.user_id', '', true)"))
    assert connection.scalar(text('SELECT count(*) FROM accounts')) == 0
    connection.exec_driver_sql('RESET ROLE')
    for role in ('anon', 'authenticated'):
        assert not connection.scalar(text("SELECT has_table_privilege(:role, 'accounts', 'SELECT')"), {'role': role})
        assert not connection.scalar(text("SELECT has_table_privilege(:role, 'payments', 'INSERT')"), {'role': role})
    assert connection.scalar(text("SELECT count(*) FROM pg_tables t JOIN pg_class c ON c.relname=t.tablename JOIN pg_namespace n ON n.oid=c.relnamespace AND n.nspname=t.schemaname WHERE t.schemaname='public' AND t.tablename <> 'alembic_version' AND c.relrowsecurity AND c.relforcerowsecurity")) == 10
