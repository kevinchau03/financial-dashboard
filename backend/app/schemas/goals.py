from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    account_id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1, max_length=120)
    target_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    due_date: date | None = None
    description: str | None = Field(default=None, max_length=2000)


class GoalRead(GoalCreate):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    account_name: str | None = None


class GoalUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    account_id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1, max_length=120)
    target_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    due_date: date | None = None
    description: str | None = Field(default=None, max_length=2000)


class GoalContribution(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
