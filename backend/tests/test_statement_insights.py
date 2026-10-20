from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app import main
from app.models import StatementImport


def test_insights_are_scoped_and_work_with_missing_debit_or_credit(client):
    def upload(data):
        response = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('test.csv', data)})
        assert response.status_code == 200
        return response.json()['statement_id']
    first = upload(b'2026-01-01,Cafe,10,,90\n2026-01-02,Cafe,20,,70\n2026-01-02,Pay,,100,170')
    upload(b'2026-02-01,Other,999,,100')
    response = client.get(f'/api/statements/{first}/insights')
    assert response.status_code == 200
    data = response.json()
    assert {key: value for key, value in data.items() if key not in ('largest_transaction', 'highest_spending_day')} == {'statement_id': first, 'start_date': '2026-01-01', 'end_date': '2026-01-02', 'total_income': '100.00', 'total_spent': '30.00', 'total_transactions': 3, 'most_frequent_transaction_name': 'Cafe', 'most_frequent_transaction_count': 2}
    assert data['largest_transaction']['amount'] == '100.00'
    assert data['largest_transaction']['kind'] == 'credit'
    assert data['largest_transaction']['description'] == 'Pay'
    day = data['highest_spending_day']
    assert day['date'] == '2026-01-02'
    assert day['total_spent'] == '20.00'
    assert [(row['description'], row['debit'], row['credit']) for row in day['transactions']] == [('Cafe', '20.00', None), ('Pay', None, '100.00')]
    assert client.get('/api/statements/999999/insights').status_code == 404


def test_credit_only_and_tied_insights(client):
    def upload(data):
        return client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('test.csv', data)}).json()['statement_id']
    credit = upload(b'2026-01-01,Pay,,100,100')
    data = client.get(f'/api/statements/{credit}/insights').json()
    assert data['highest_spending_day'] is None
    assert data['largest_transaction']['amount'] == '100.00'
    assert data['largest_transaction']['kind'] == 'credit'
    tied = upload(b'2026-01-02,Zebra,10,,100\n2026-01-01,Apple,10,,90')
    data = client.get(f'/api/statements/{tied}/insights').json()
    assert data['highest_spending_day']['date'] == '2026-01-01'
    assert data['largest_transaction']['kind'] == 'debit'
    assert data['largest_transaction']['date'] == '2026-01-01'
    assert [row['description'] for row in data['highest_spending_day']['transactions']] == ['Apple']
    assert data['most_frequent_transaction_name'] == 'Apple'
    assert data['most_frequent_transaction_count'] == 1


def test_empty_statement_insights(client):
    with Session(main.engine) as session:
        item = StatementImport(filename='empty.csv', content_hash='empty', imported_at=datetime.now(timezone.utc))
        session.add(item)
        session.commit()
        statement_id = item.id
    response = client.get(f'/api/statements/{statement_id}/insights')
    assert response.status_code == 200
    data = response.json()
    assert data['total_transactions'] == 0
    assert data['largest_transaction'] is None
    assert data['most_frequent_transaction_name'] is None
    assert data['most_frequent_transaction_count'] == 0
    assert data['highest_spending_day'] is None


def test_largest_direction_and_day_details_with_both_columns_present(client):
    csv = b'2026-01-01,Purchase,200,10,0\n2026-01-01,Refund,,15,15\n2026-01-02,Other,20,,0'
    statement_id = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('both.csv', csv)}).json()['statement_id']
    data = client.get(f'/api/statements/{statement_id}/insights').json()
    assert data['largest_transaction']['kind'] == 'debit'
    assert data['largest_transaction']['amount'] == '200.00'
    assert data['highest_spending_day']['total_spent'] == '200.00'
    assert len(data['highest_spending_day']['transactions']) == 2
