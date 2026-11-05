"""Add debt types and optional credit/payment metadata without changing balances."""
from alembic import op
import sqlalchemy as sa

revision = '20261102_01'
down_revision = '20261022_01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('debts', sa.Column('debt_type', sa.String(30), nullable=False, server_default='personal_debt'))
    for name in ('credit_limit', 'minimum_payment', 'payment_amount'):
        op.add_column('debts', sa.Column(name, sa.Numeric(14, 2), nullable=True))
    op.add_column('debts', sa.Column('payment_frequency', sa.String(20), nullable=True))


def downgrade():
    for name in ('payment_frequency', 'payment_amount', 'minimum_payment', 'credit_limit', 'debt_type'):
        op.drop_column('debts', name)
