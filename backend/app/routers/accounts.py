from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_session
from app.models import Account

from app.schemas.accounts import AccountInput, AccountRead

router = APIRouter(prefix='/api/accounts', tags=['accounts'])

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
