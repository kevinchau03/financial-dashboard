"""Manual account balances, independent from goal allocations and CSV imports."""
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_session
from models import Account

router = APIRouter(prefix='/api/accounts', tags=['accounts'])


class AccountInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    name: str = Field(min_length=1, max_length=120)
    account_type: Literal['Savings', 'Chequing', 'TFSA', 'FHSA', 'RRSP', 'Other']
    balance: Decimal = Field(max_digits=14, decimal_places=2)


class AccountRead(AccountInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


@router.get('', response_model=list[AccountRead])
def list_accounts(session: Annotated[Session, Depends(get_session)]):
    return session.scalars(select(Account).order_by(Account.id.desc())).all()


@router.post('', response_model=AccountRead, status_code=201)
def create_account(payload: AccountInput, session: Annotated[Session, Depends(get_session)]):
    account = Account(**payload.model_dump())
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.put('/{account_id}', response_model=AccountRead)
def update_account(account_id: int, payload: AccountInput, session: Annotated[Session, Depends(get_session)]):
    account = session.get(Account, account_id)
    if account is None:
        raise HTTPException(404, 'Account not found')
    for field, value in payload.model_dump().items():
        setattr(account, field, value)
    session.commit()
    session.refresh(account)
    return account
