import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app import main
from app import database
from app.database import UserSession
from app.auth import AuthUser, get_current_user
from uuid import UUID
from sqlalchemy import event
from app.database import Owned

TEST_USER_ID = UUID("00000000-0000-4000-8000-000000000001")


@pytest.fixture(autouse=True)
def seed_owner(monkeypatch):
    # Domain tests that seed records through an administrative Session must name an owner.
    def assign_test_owner(session, *_):
        if isinstance(session, UserSession):
            return
        for row in session.new:
            if isinstance(row, Owned) and row.user_id is None:
                row.user_id = TEST_USER_ID
    event.listen(Session, "before_flush", assign_test_owner)
    initialize = main.initialize_database
    monkeypatch.setattr(main, 'initialize_database', lambda target: initialize(target, legacy_owner=TEST_USER_ID))
    yield
    event.remove(Session, "before_flush", assign_test_owner)


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(database, "engine", engine)
    main.app.dependency_overrides[get_current_user] = lambda: AuthUser(TEST_USER_ID, "test@example.com")
    try:
        with TestClient(main.app) as client:
            yield client
    finally:
        main.app.dependency_overrides.clear()
        engine.dispose()
