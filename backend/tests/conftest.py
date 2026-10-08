import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app import main
from app.database import get_session

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
    try:
        with TestClient(main.app) as client:
            yield client
    finally:
        main.app.dependency_overrides.clear()
        engine.dispose()
