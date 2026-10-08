from typing import Annotated
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_session
from app.services.analytics import get_total_savings, get_total_goal_contributions, get_total_debt, get_total_bills

router = APIRouter(tags=['analytics'])

@router.get("/api/analytics/savings", response_model=dict[str, Decimal])
def total_savings(session: Annotated[Session, Depends(get_session)]):
    return {"total_savings": get_total_savings(session)}

@router.get("/api/analytics/goals/contributions", response_model=dict[str, Decimal])
def total_goal_contributions(session: Annotated[Session, Depends(get_session)]):
    return {"total_goal_contributions": get_total_goal_contributions(session)}

@router.get("/api/analytics/debts", response_model=dict[str, Decimal])
def total_debts(session: Annotated[Session, Depends(get_session)]):
    return {"total_debt": get_total_debt(session)}

@router.get("/api/analytics/bills", response_model=dict[str, Decimal])
def total_bills(session: Annotated[Session, Depends(get_session)]):
    return {"total_bills": get_total_bills(session)}
