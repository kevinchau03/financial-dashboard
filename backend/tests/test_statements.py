from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app import main
from app.models import StatementImport


def upload(client, contents, filename='statement.csv'):
    response = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': (filename, contents, 'text/csv')})
    assert response.status_code == 200
    return response.json()


def test_library_and_reopened_statements_are_independent(client):
    assert client.get('/api/statements').json() == {'items': [], 'total': 0}
    first = upload(client, b'06/08/2026,Cafe,2.50,,100\n2026-06-09,Pay,,50,150', 'june.csv')
    second = upload(client, b'07/10/2026,Rent,90,,60', 'july.csv')
    listing = client.get('/api/statements').json()
    assert listing['total'] == 2
    assert [item['filename'] for item in listing['items']] == ['july.csv', 'june.csv']
    assert listing['items'][1]['row_count'] == 2
    assert listing['items'][1]['start_date'] == '2026-06-08'
    assert listing['items'][1]['end_date'] == '2026-06-09'
    assert listing['items'][1]['has_file'] is True
    # A new app lifecycle can retrieve data without the upload response.
    with TestClient(main.app) as reopened:
        detail = reopened.get(f"/api/statements/{first['statement_id']}").json()
        assert detail['rows'] == first['rows']
        assert detail['stats'] == first['stats']
        assert detail['filename'] == 'june.csv'
        assert reopened.get(f"/api/statements/{second['statement_id']}").json()['stats']['total_spent'] == '90.00'


def test_original_file_download_and_duplicates(client):
    contents = b'\xef\xbb\xbf06/08/2026,"Cafe, Inc",2.5,,100\r\n'
    saved = upload(client, contents, 'été.csv')
    response = client.get(f"/api/statements/{saved['statement_id']}/file")
    assert response.content == contents
    assert response.headers['content-type'].startswith('text/csv')
    assert response.headers['content-disposition'] == "attachment; filename*=UTF-8''%C3%A9t%C3%A9.csv"
    duplicate = upload(client, contents, 'renamed.csv')
    assert duplicate['statement_id'] == saved['statement_id']
    assert duplicate['already_imported'] is True
    assert client.get('/api/statements').json()['total'] == 1


def test_summary_returns_one_statement_stats_without_transactions(client):
    first = upload(client, b'06/08/2026,Cafe,2.50,,100\n2026-06-09,Pay,,50,150')
    upload(client, b'07/10/2026,Rent,90,,60')
    response = client.get(f"/api/statements/{first['statement_id']}/summary")
    assert response.status_code == 200
    assert response.json() == {'statement_id': first['statement_id'], 'stats': first['stats']}
    assert client.get('/api/statements/999/summary').status_code == 404


def test_older_statement_still_opens_and_reupload_restores_file(client):
    contents = b'06/08/2026,Cafe,2.50,,100'
    saved = upload(client, contents)
    with Session(main.engine) as session:
        session.get(StatementImport, saved['statement_id']).csv_contents = None
        session.commit()
    assert client.get(f"/api/statements/{saved['statement_id']}").json()['has_file'] is False
    assert client.get(f"/api/statements/{saved['statement_id']}/file").status_code == 404
    upload(client, contents)
    assert client.get(f"/api/statements/{saved['statement_id']}/file").content == contents
    assert client.get('/api/statements').json()['total'] == 1


def test_library_pagination_and_missing_statements(client):
    for day in range(1, 4):
        upload(client, f'06/0{day}/2026,Cafe,1,,100'.encode(), f'{day}.csv')
    assert client.get('/api/statements?limit=2').json()['total'] == 3
    assert len(client.get('/api/statements?offset=2&limit=2').json()['items']) == 1
    assert client.get('/api/statements?offset=3').json()['items'] == []
    assert client.get('/api/statements?offset=-1').status_code == 422
    assert client.get('/api/statements?limit=101').status_code == 422
    assert client.get('/api/statements/999').status_code == 404
    assert client.get('/api/statements/999/file').status_code == 404


def test_startup_preserves_old_statement_schema(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}", connect_args={'check_same_thread': False})
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE statement_imports (id INTEGER PRIMARY KEY, filename TEXT NOT NULL, content_hash VARCHAR(64) UNIQUE NOT NULL, imported_at DATETIME NOT NULL)'))
        connection.execute(text("INSERT INTO statement_imports VALUES (1, 'old.csv', 'hash', '2026-01-01 00:00:00')"))
    monkeypatch.setattr(main, 'engine', engine)
    with TestClient(main.app):
        with Session(engine) as session:
            old = session.get(StatementImport, 1)
            assert old.filename == 'old.csv'
            assert old.csv_contents is None
    engine.dispose()
