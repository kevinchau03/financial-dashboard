from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, Numeric, String, Text, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    account_type: Mapped[str] = mapped_column(String(30))
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2))


class Paycheque(Base):
    __tablename__ = "paycheques"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    received_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    allocated_cents: Mapped[int] = mapped_column(default=0, server_default='0')
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True, unique=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    allocations: Mapped[list['PaychequeAllocation']] = relationship(lazy='selectin', order_by='PaychequeAllocation.id')

    @property
    def allocated_amount(self) -> Decimal:
        return (Decimal(self.allocated_cents) / 100).quantize(Decimal('.01'))

    @property
    def remaining_amount(self) -> Decimal:
        return self.amount - self.allocated_amount


class PaychequeAllocationBatch(Base):
    __tablename__ = 'paycheque_allocation_batches'

    id: Mapped[int] = mapped_column(primary_key=True)
    paycheque_id: Mapped[int] = mapped_column(ForeignKey('paycheques.id'), index=True)
    request_id: Mapped[str] = mapped_column(String(36), unique=True)
    fingerprint: Mapped[str] = mapped_column(String(64))


class PaychequeAllocation(Base):
    __tablename__ = 'paycheque_allocations'

    id: Mapped[int] = mapped_column(primary_key=True)
    paycheque_id: Mapped[int] = mapped_column(ForeignKey('paycheques.id'), index=True)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey('financial_goals.id', ondelete='SET NULL'), nullable=True)
    debt_id: Mapped[int | None] = mapped_column(ForeignKey('debts.id', ondelete='SET NULL'), nullable=True)
    kind: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(120))
    amount_cents: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(12), default='planned')
    completed_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    @property
    def amount(self) -> Decimal:
        return (Decimal(self.amount_cents) / 100).quantize(Decimal('.01'))


class StatementImport(Base):
    __tablename__ = "statement_imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csv_contents: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    statement_id: Mapped[int] = mapped_column(ForeignKey("statement_imports.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(Text)
    debit_cents: Mapped[int | None] = mapped_column(nullable=True)
    credit_cents: Mapped[int | None] = mapped_column(nullable=True)
    balance_cents: Mapped[int]


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    current_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

class Bills(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    recurring: Mapped[bool] = mapped_column(nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_paid: Mapped[bool] = mapped_column(default=False, server_default="0")
    recurrence_day: Mapped[int | None] = mapped_column(nullable=True)
    payments: Mapped[list["BillPayment"]] = relationship(order_by="desc(BillPayment.paid_on), desc(BillPayment.id)", lazy="selectin", cascade="all, delete-orphan")


class BillPayment(Base):
    __tablename__ = "bill_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    paid_on: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

class Debts(Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    current_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payments: Mapped[list["DebtPayment"]] = relationship(order_by="desc(DebtPayment.paid_on), desc(DebtPayment.id)", lazy="selectin", cascade="all, delete-orphan")

    @property
    def remaining_amount(self) -> Decimal:
        return self.amount - self.current_amount

class DebtPayment(Base):
    __tablename__ = "debt_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    debt_id: Mapped[int] = mapped_column(ForeignKey("debts.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    paid_on: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
