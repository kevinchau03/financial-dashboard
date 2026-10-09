from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class AccountInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    name: str = Field(min_length=1, max_length=120)
    account_type: Literal['Savings', 'Chequing', 'TFSA', 'FHSA', 'RRSP', 'Other']
    balance: Decimal = Field(max_digits=14, decimal_places=2)

class AccountRead(AccountInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    earmarked_amount: Decimal
    available_amount: Decimal
    goal_summary: list[dict]
