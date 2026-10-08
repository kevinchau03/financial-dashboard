import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import main


@pytest.mark.parametrize('kind,payload,payment_table', [
    ('goals', {'name': 'Trip', 'target_amount': '100', 'current_amount': '20'}, None),
    ('bills', {'name': 'Internet', 'amount': '100'}, 'bill_payments'),
    ('debts', {'name': 'Loan', 'amount': '100'}, 'debt_payments'),
])
def test_delete_removes_only_selected_item_and_payments(client, kind, payload, payment_table):
    first = client.post(f'/api/{kind}', json=payload).json()
    other = client.post(f'/api/{kind}', json=payload).json()
    if payment_table:
        for item in (first, other):
            assert client.post(f"/api/{kind}/{item['id']}/payments", json={
                'amount': '10', 'paid_on': '2025-01-01',
            }).status_code == 201
    response = client.delete(f"/api/{kind}/{first['id']}")
    assert response.status_code == 204
    assert response.content == b''
    remaining = client.get(f'/api/{kind}').json()
    assert [item['id'] for item in remaining] == [other['id']]
    if payment_table:
        assert len(remaining[0]['payments']) == 1
        with Session(main.engine) as session:
            assert session.execute(text(f'SELECT COUNT(*) FROM {payment_table}')).scalar_one() == 1
    assert client.delete(f"/api/{kind}/{first['id']}").status_code == 404
    assert client.delete(f'/api/{kind}/99999').status_code == 404
    metric, field, expected = {
        'goals': ('savings', 'total_savings', '20.00'),
        'bills': ('bills', 'total_bills', '100.00'),
        'debts': ('debts', 'total_debt', '90.00'),
    }[kind]
    assert client.get(f'/api/analytics/{metric}').json()[field] == expected
