from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


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
