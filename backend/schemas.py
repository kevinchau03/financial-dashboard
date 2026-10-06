from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AllocationCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['goal', 'debt']
    target_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class PaychequeCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    received_on: date = Field(default_factory=date.today)
    request_id: UUID | None = None
    allocations: list[AllocationCreate] = Field(default_factory=list, max_length=200)


class AllocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: Literal['goal', 'debt']
    name: str
    goal_id: int | None
    debt_id: int | None
    amount: Decimal
    status: Literal['planned', 'completed', 'cancelled']
    completed_on: date | None


class PaychequeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: Decimal
    received_on: date | None
    allocated_amount: Decimal
    remaining_amount: Decimal
    allocations: list[AllocationRead]


class AllocationBatchCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    allocations: list[AllocationCreate] = Field(min_length=1, max_length=200)


class AllocationComplete(BaseModel):
    model_config = ConfigDict(extra='forbid')
    completed_on: date


# Financial Goals
class GoalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    target_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    due_date: date | None = None
    description: str | None = Field(default=None, max_length=2000)


class GoalRead(GoalCreate):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int

class GoalUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    target_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    due_date: date | None = None
    description: str | None = Field(default=None, max_length=2000)


class GoalContribution(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


# Bills
class BillCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    due_date: date | None = None
    recurring: bool = Field(default=False)
    description: str | None = Field(default=None, max_length=2000)

class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: Decimal
    paid_on: date
    due_date: date | None


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    paid_on: date
    next_due_date: date | None = None


class BillRead(BillCreate):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    is_paid: bool
    payments: list[PaymentRead] = Field(default_factory=list)

class DebtCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    due_date: date | None = None
    interest_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_balance(self):
        if self.current_amount > self.amount:
            raise ValueError("Amount already paid cannot exceed the total debt.")
        return self

class DebtRead(DebtCreate):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    remaining_amount: Decimal
    payments: list[PaymentRead] = Field(default_factory=list)


class DebtUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    due_date: date | None = None
    interest_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    description: str | None = Field(default=None, max_length=2000)


class DebtPaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    paid_on: date
