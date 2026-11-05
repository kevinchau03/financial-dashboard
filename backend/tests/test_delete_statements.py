from uuid import UUID

import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import main
from app.auth import AuthUser, get_current_user
from app.models import StatementImport, Transaction
from app.services.statements import delete_statement
from conftest import TEST_USER_ID


def upload(client, contents):
    result = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('test.csv', contents)})
    assert result.status_code == 200
    return result.json()['statement_id']


def test_delete_statement_removes_only_its_transactions_and_allows_reupload(client):
    contents = b'2026-01-01,Cafe,10,,\n2026-01-02,Pay,,100,'
    first = upload(client, contents)
    second = upload(client, b'2026-02-01,Rent,50,,')
    assert client.delete(f'/api/statements/{first}').status_code == 204
    assert client.delete(f'/api/statements/{first}').status_code == 404
    for suffix in ('', '/file', '/summary', '/insights'):
        assert client.get(f'/api/statements/{first}{suffix}').status_code == 404
    assert client.get('/api/statements').json()['total'] == 1
    assert client.get(f'/api/statements/{second}').json()['row_count'] == 1
    with Session(main.engine) as session:
        assert session.scalar(select(func.count()).select_from(Transaction).where(Transaction.statement_id == first)) == 0
        assert session.get(StatementImport, first) is None
        assert session.scalar(select(func.count()).select_from(Transaction)) == 1
    restored = upload(client, contents)
    assert client.get(f'/api/statements/{restored}').json()['row_count'] == 2
    assert client.delete(f'/api/statements/{second}').status_code == 204
    assert client.delete(f'/api/statements/{restored}').status_code == 204
    assert client.get('/api/statements').json() == {'items': [], 'total': 0}


def test_other_user_cannot_delete_statement(client):
    statement_id = upload(client, b'2026-01-01,Private,10,,')
    main.app.dependency_overrides[get_current_user] = lambda: AuthUser(UUID('00000000-0000-4000-8000-000000000002'), 'second@example.test')
    assert client.delete(f'/api/statements/{statement_id}').status_code == 404
    main.app.dependency_overrides[get_current_user] = lambda: AuthUser(TEST_USER_ID, 'first@example.test')
    assert client.get(f'/api/statements/{statement_id}').json()['row_count'] == 1


def test_failed_statement_delete_rolls_back_transactions(client, monkeypatch):
    statement_id = upload(client, b'2026-01-01,Keep,10,,')
    with Session(main.engine) as session:
        def fail_commit():
            raise RuntimeError('Simulated commit failure')
        monkeypatch.setattr(session, 'commit', fail_commit)
        with pytest.raises(RuntimeError, match='Simulated'):
            delete_statement(statement_id, session)
    assert client.get(f'/api/statements/{statement_id}').json()['row_count'] == 1
