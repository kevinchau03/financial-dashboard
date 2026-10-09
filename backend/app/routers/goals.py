from typing import Annotated
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.database import get_session
from app.models import FinancialGoal
from app.services.common import get_or_404
from app.services.paycheques import detach_target
from app.services.goals import check_assignment, lock_account
from app.schemas.goals import GoalCreate, GoalRead, GoalUpdate, GoalContribution

router = APIRouter(tags=['goals'])

@router.get("/api/goals", response_model=list[GoalRead])
def list_goals(session: Annotated[Session, Depends(get_session)]):
    return session.scalars(select(FinancialGoal).order_by(FinancialGoal.id.desc())).all()


@router.post("/api/goals", response_model=GoalRead, status_code=201)
def create_goal(goal: GoalCreate, session: Annotated[Session, Depends(get_session)]):
    check_assignment(session, goal.account_id, goal.current_amount)
    saved_goal = FinancialGoal(**goal.model_dump())
    session.add(saved_goal)
    session.commit()
    session.refresh(saved_goal)
    return saved_goal


@router.delete("/api/goals/{item_id}", status_code=204)
def delete_goal(item_id: int, session: Annotated[Session, Depends(get_session)]):
    detach_target(session, 'goal', item_id)
    session.delete(get_or_404(session, FinancialGoal, item_id))
    session.commit()


@router.put("/api/goals/{goal_id}", response_model=GoalRead)
def update_goal(goal_id: int, goal: GoalUpdate, session: Annotated[Session, Depends(get_session)]):
    saved = get_or_404(session, FinancialGoal, goal_id)
    if goal.account_id is not None:
        lock_account(session, goal.account_id)
        session.refresh(saved)
    account_id = goal.account_id if 'account_id' in goal.model_fields_set else saved.account_id
    check_assignment(session, account_id, saved.current_amount, saved.id)
    for field, value in goal.model_dump(exclude_unset=True).items():
        setattr(saved, field, value)
    session.commit()
    session.refresh(saved)
    return saved


@router.post("/api/goals/{goal_id}/contributions", response_model=GoalRead)
def add_to_goal(goal_id: int, contribution: GoalContribution, session: Annotated[Session, Depends(get_session)]):
    saved = get_or_404(session, FinancialGoal, goal_id)
    if saved.account_id is not None:
        lock_account(session, saved.account_id)
        session.refresh(saved)
        check_assignment(session, saved.account_id, saved.current_amount + contribution.amount, saved.id)
    # Increment in the database so concurrent contributions cannot overwrite each other.
    result = session.execute(update(FinancialGoal).where(
        FinancialGoal.id == goal_id,
        FinancialGoal.current_amount <= Decimal("999999999999.99") - contribution.amount,
    ).values(current_amount=FinancialGoal.current_amount + contribution.amount))
    if result.rowcount == 0:
        get_or_404(session, FinancialGoal, goal_id)
        raise HTTPException(422, "This addition would exceed the maximum supported balance.")
    session.commit()
    return get_or_404(session, FinancialGoal, goal_id)
