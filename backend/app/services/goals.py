"""Account-backed goals earmark existing balances; deposits are recorded separately."""
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session
from app.models import Account, FinancialGoal


def lock_account(session: Session, account_id: int):
    result = session.execute(update(Account).where(Account.id == account_id).values(balance=Account.balance))
    if result.rowcount == 0:
        raise HTTPException(404, 'Account not found.')
    account = session.get(Account, account_id)
    session.refresh(account)
    return account


def earmarked(session: Session, account_id: int, exclude_goal: int | None = None) -> Decimal:
    query = select(func.coalesce(func.sum(FinancialGoal.current_amount), 0)).where(FinancialGoal.account_id == account_id)
    if exclude_goal is not None:
        query = query.where(FinancialGoal.id != exclude_goal)
    return Decimal(session.scalar(query)).quantize(Decimal('.01'))


def check_assignment(session: Session, account_id: int | None, amount: Decimal, exclude_goal: int | None = None):
    if account_id is None:
        return
    account = lock_account(session, account_id)
    if earmarked(session, account_id, exclude_goal) + amount > account.balance:
        raise HTTPException(422, 'This account does not have enough unassigned money for the goal. Reduce the amount or update its recorded balance first.')
