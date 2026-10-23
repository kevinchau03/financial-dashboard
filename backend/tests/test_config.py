import pytest
from app.config import database_url


@pytest.mark.parametrize('setting', [('VERCEL', '1'), ('VERCEL_ENV', 'production'), ('VERCEL_ENV', 'preview')])
@pytest.mark.parametrize('value', [None, '', '   ', 'sqlite:///goals.db'])
def test_vercel_requires_postgres(monkeypatch, setting, value):
    monkeypatch.delenv('VERCEL', raising=False)
    monkeypatch.delenv('VERCEL_ENV', raising=False)
    monkeypatch.setenv(*setting)
    if value is None:
        monkeypatch.delenv('DATABASE_URL', raising=False)
    else:
        monkeypatch.setenv('DATABASE_URL', value)
    with pytest.raises(ValueError, match='DATABASE_URL'):
        database_url()


def test_vercel_accepts_postgres_without_exposing_credentials(monkeypatch):
    monkeypatch.setenv('VERCEL', '1')
    value = 'postgresql://test:dummy-password@pooler.example.test:6543/postgres'
    monkeypatch.setenv('DATABASE_URL', value)
    assert database_url() == value


def test_local_sqlite_fallback_is_preserved(monkeypatch):
    for key in ('VERCEL', 'VERCEL_ENV', 'DATABASE_URL'):
        monkeypatch.delenv(key, raising=False)
    assert database_url().startswith('sqlite:///')
