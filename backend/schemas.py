from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PaychequeCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class PaychequeRead(PaychequeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


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
