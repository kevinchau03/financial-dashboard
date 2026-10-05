import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import main
from database import Base, get_session


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    monkeypatch.setattr(main, "engine", engine)

    def session_override():
        with Session(engine) as session:
            yield session

    main.app.dependency_overrides[get_session] = session_override
    with TestClient(main.app) as client:
        yield client
    main.app.dependency_overrides.clear()
    engine.dispose()


def test_create_and_persist_goal(client):
    assert client.get('/api/goals').json() == []
    payload = {
        'name': '  Emergency fund  ',
        'target_amount': '5000.25',
        'current_amount': '125.10',
        'due_date': '2027-09-01',
        'description': 'Three months of expenses',
    }
    response = client.post('/api/goals', json=payload)
    assert response.status_code == 201
    saved = response.json()
    assert saved == {**payload, 'name': 'Emergency fund', 'id': saved['id']}
    # A fresh application lifecycle and DB session must still see the saved goal.
    with TestClient(main.app) as restarted:
        assert restarted.get('/api/goals').json() == [saved]


def test_optional_fields_and_default_amount(client):
    response = client.post('/api/goals', json={'name': 'Trip', 'target_amount': '100'})
    assert response.status_code == 201
    assert response.json()['current_amount'] == '0.00'
    assert response.json()['due_date'] is None
    assert response.json()['description'] is None
    # Exceeding the target is a valid completed goal.
    assert client.post('/api/goals', json={
        'name': 'Done', 'target_amount': '10', 'current_amount': '15',
    }).status_code == 201


@pytest.mark.parametrize('changes', [
    {'name': '   '}, {'name': 'x' * 121}, {'target_amount': '0'},
    {'target_amount': '-1'}, {'current_amount': '-1'},
    {'target_amount': '1.001'}, {'current_amount': '0.001'},
    {'target_amount': '1000000000000'}, {'target_amount': 'NaN'},
    {'due_date': '2027-02-30'}, {'description': 'x' * 2001},
])
def test_reject_invalid_goal(client, changes):
    response = client.post('/api/goals', json={
        'name': 'Savings', 'target_amount': '100', **changes,
    })
    assert response.status_code == 422
    assert client.get('/api/goals').json() == []

