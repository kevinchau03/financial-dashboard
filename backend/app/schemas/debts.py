from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.bills import PaymentRead


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
