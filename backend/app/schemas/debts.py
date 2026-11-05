from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.payments import PaymentRead


DebtType = Literal['credit_card', 'line_of_credit', 'personal_loan', 'auto_loan', 'student_loan', 'mortgage', 'buy_now_pay_later', 'personal_debt']
PaymentFrequency = Literal['weekly', 'biweekly', 'semimonthly', 'monthly', 'quarterly', 'annually']


class DebtMetadata(BaseModel):
    debt_type: DebtType = 'personal_debt'
    credit_limit: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    minimum_payment: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    payment_amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    payment_frequency: PaymentFrequency | None = None


class DebtCreate(DebtMetadata):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    due_date: date | None = None
    interest_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode='after')
    def validate_metadata(self):
        revolving = self.debt_type in ('credit_card', 'line_of_credit')
        if revolving and (self.payment_amount is not None or self.payment_frequency is not None):
            raise ValueError('Use minimum payment for a credit card or line of credit.')
        if not revolving and (self.credit_limit is not None or self.minimum_payment is not None):
            raise ValueError('Credit limit and minimum payment apply only to credit cards and lines of credit.')
        if (self.payment_amount is None) != (self.payment_frequency is None):
            raise ValueError('Provide both a recurring payment amount and a payment frequency.')
        return self

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


class DebtUpdate(DebtMetadata):
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
