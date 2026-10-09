from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AllocationCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['goal', 'debt', 'account']
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
    kind: Literal['goal', 'debt', 'account']
    name: str
    goal_id: int | None
    debt_id: int | None
    account_id: int | None
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
