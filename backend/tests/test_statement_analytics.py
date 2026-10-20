from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app import main
from app.services.analytics import get_total_spent, get_total_income, get_time_range, get_total_transactions

FUNCTIONS = [get_total_spent, get_total_income, get_time_range, get_total_transactions]


@pytest.mark.parametrize('function', FUNCTIONS)
def test_statement_id_is_required(client, function):
    with Session(main.engine) as session:
        with pytest.raises(TypeError):
            function(session)
        for invalid in [None, 0, -1, True, '1']:
            with pytest.raises(ValueError, match='statement ID'):
                function(session, invalid)


def test_every_metric_stays_with_its_statement(client):
    def upload(contents):
        response = client.post('/api/upload_csv', data={'format': 'td'}, files={'file': ('statement.csv', contents)})
        assert response.status_code == 200
        return response.json()['statement_id']
    first = upload(b'2026-01-01,Shop,10,,90\n2026-01-02,Pay,,25,115')
    second = upload(b'2026-02-01,Other,50,,65')
    with Session(main.engine) as session:
        assert get_total_spent(session, first) == Decimal('10.00')
        assert get_total_income(session, first) == Decimal('25.00')
        assert get_time_range(session, first) == ('2026-01-01', '2026-01-02')
        assert get_total_transactions(session, first) == 2
        assert get_total_spent(session, second) == Decimal('50.00')
        assert get_total_income(session, second) == Decimal('0.00')
        assert get_time_range(session, second) == ('2026-02-01', '2026-02-01')
        assert get_total_transactions(session, second) == 1
