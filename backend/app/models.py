from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, Numeric, String, Text, ForeignKey, LargeBinary, CheckConstraint, Index, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, Owned


class Account(Owned, Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    account_type: Mapped[str] = mapped_column(String(30))
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    goals: Mapped[list['FinancialGoal']] = relationship(back_populates='account', lazy='selectin')

    @property
    def earmarked_amount(self) -> Decimal:
        return sum((goal.current_amount for goal in self.goals), Decimal('0.00'))

    @property
    def available_amount(self) -> Decimal:
        return self.balance - self.earmarked_amount

    @property
    def goal_summary(self) -> list[dict]:
        return [{'id': goal.id, 'name': goal.name, 'current_amount': str(goal.current_amount),
                 'target_amount': str(goal.target_amount)} for goal in self.goals]



class Paycheque(Owned, Base):
    __table_args__ = (UniqueConstraint('user_id', 'request_id', name='uq_paycheque_user_request'),)
    __tablename__ = "paycheques"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    received_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    bills_reserved: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, server_default='0')
    spending_reserved: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, server_default='0')
    next_payday: Mapped[date | None] = mapped_column(Date, nullable=True)
    allocated_cents: Mapped[int] = mapped_column(default=0, server_default='0')
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    allocations: Mapped[list['PaychequeAllocation']] = relationship(lazy='selectin', order_by='PaychequeAllocation.id')

    @property
    def allocated_amount(self) -> Decimal:
        return (Decimal(self.allocated_cents) / 100).quantize(Decimal('.01'))

    @property
    def remaining_amount(self) -> Decimal:
        return self.amount - self.allocated_amount - self.bills_reserved - self.spending_reserved


class PaychequeAllocationBatch(Owned, Base):
    __table_args__ = (UniqueConstraint('user_id', 'request_id', name='uq_batch_user_request'),)
    __tablename__ = 'paycheque_allocation_batches'

    id: Mapped[int] = mapped_column(primary_key=True)
    paycheque_id: Mapped[int] = mapped_column(ForeignKey('paycheques.id'), index=True)
    request_id: Mapped[str] = mapped_column(String(36))
    fingerprint: Mapped[str] = mapped_column(String(64))


class PaychequeAllocation(Owned, Base):
    __tablename__ = 'paycheque_allocations'

    id: Mapped[int] = mapped_column(primary_key=True)
    paycheque_id: Mapped[int] = mapped_column(ForeignKey('paycheques.id'), index=True)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey('financial_goals.id', ondelete='SET NULL'), nullable=True)
    debt_id: Mapped[int | None] = mapped_column(ForeignKey('debts.id', ondelete='SET NULL'), nullable=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    kind: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(120))
    amount_cents: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(12), default='planned')
    completed_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    @property
    def amount(self) -> Decimal:
        return (Decimal(self.amount_cents) / 100).quantize(Decimal('.01'))


class StatementImport(Owned, Base):
    __table_args__ = (UniqueConstraint('user_id', 'content_hash', name='uq_statement_user_hash'),)
    __tablename__ = "statement_imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    csv_contents: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class Transaction(Owned, Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    statement_id: Mapped[int] = mapped_column(ForeignKey("statement_imports.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(Text)
    debit_cents: Mapped[int | None] = mapped_column(nullable=True)
    credit_cents: Mapped[int | None] = mapped_column(nullable=True)
    balance_cents: Mapped[int]


class FinancialGoal(Owned, Base):
    __tablename__ = "financial_goals"

    account_id: Mapped[int | None] = mapped_column(ForeignKey('accounts.id'), nullable=True)
    account: Mapped[Account | None] = relationship(back_populates='goals', lazy='selectin')

    @property
    def account_name(self) -> str | None:
        return self.account.name if self.account else None

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    current_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

class Bills(Owned, Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    recurring: Mapped[bool] = mapped_column(nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_paid: Mapped[bool] = mapped_column(default=False, server_default="0")
    recurrence_day: Mapped[int | None] = mapped_column(nullable=True)
    payments: Mapped[list['Payment']] = relationship(primaryjoin='and_(Bills.id == Payment.bill_id, Payment.undone_at.is_(None))', order_by='desc(Payment.paid_on), desc(Payment.id)', lazy='selectin')


class Debts(Owned, Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    current_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payments: Mapped[list['Payment']] = relationship(primaryjoin='and_(Debts.id == Payment.debt_id, Payment.undone_at.is_(None))', order_by='desc(Payment.paid_on), desc(Payment.id)', lazy='selectin')

    @property
    def remaining_amount(self) -> Decimal:
        return self.amount - self.current_amount

class Payment(Owned, Base):
    """Completed records and undo tombstones; names survive rename/deletion.

    Nullable, real foreign keys retain referential integrity without deleting history.
    An allocation can produce at most one payment. No balance is inferred from this ledger.
    """
    __tablename__ = 'payments'
    __table_args__ = (
        CheckConstraint('amount > 0 AND amount <= 999999999999.99', name='payment_positive_amount'),
        CheckConstraint("(kind = 'bill' AND debt_id IS NULL AND goal_id IS NULL) OR "
                        "(kind = 'debt' AND bill_id IS NULL AND goal_id IS NULL) OR "
                        "(kind = 'goal' AND bill_id IS NULL AND debt_id IS NULL)", name='payment_target_kind'),
        CheckConstraint("source IN ('manual', 'paycheque', 'legacy')", name='payment_source'),
        Index('ix_payments_chronology', 'user_id', 'paid_on', 'id'),
        Index('ix_payments_kind_chronology', 'user_id', 'kind', 'paid_on', 'id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(8))
    target_name: Mapped[str] = mapped_column(String(120))
    bill_id: Mapped[int | None] = mapped_column(ForeignKey('bills.id', ondelete='SET NULL'), index=True)
    debt_id: Mapped[int | None] = mapped_column(ForeignKey('debts.id', ondelete='SET NULL'), index=True)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey('financial_goals.id', ondelete='SET NULL'), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    paid_on: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(12), default='manual')
    allocation_id: Mapped[int | None] = mapped_column(ForeignKey('paycheque_allocations.id', ondelete='SET NULL'), unique=True)
    # Legacy history has no known recording timestamp; never invent one.
    recorded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    undo_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    undo_account_id: Mapped[int | None] = mapped_column(ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    undone_at: Mapped[datetime | None] = mapped_column(nullable=True)

    @property
    def target_id(self) -> int | None:
        return {'bill': self.bill_id, 'debt': self.debt_id, 'goal': self.goal_id}[self.kind]

    @property
    def undo_unavailable_reason(self) -> str | None:
        if self.target_id is None:
            return 'The original item has been deleted. Its history is retained.'
        if self.undo_state is None and (self.source == 'legacy' or self.kind == 'bill' or
                                       (self.kind == 'goal' and self.source == 'paycheque')):
            return 'This older payment has no complete undo details.'
        return None
