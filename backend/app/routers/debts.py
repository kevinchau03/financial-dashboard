from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.database import get_session
from app.models import Debts
from app.services.common import get_or_404
from app.services.paycheques import detach_target
from app.services import debts
from app.schemas.debts import DebtCreate, DebtRead, DebtUpdate, DebtPaymentCreate

router = APIRouter(tags=['debts'])

@router.delete("/api/debts/{item_id}", status_code=204)
def delete_debt(item_id: int, session: Annotated[Session, Depends(get_session)]):
    detach_target(session, 'debt', item_id)
    session.delete(get_or_404(session, Debts, item_id))
    session.commit()


@router.get("/api/debts", response_model=list[DebtRead])
def list_debts(session: Annotated[Session, Depends(get_session)]):
    return session.scalars(select(Debts).order_by(Debts.id.desc())).all()


@router.post("/api/debts", response_model=DebtRead, status_code=201)
def create_debt(debt: DebtCreate, session: Annotated[Session, Depends(get_session)]):
    saved = Debts(**debt.model_dump())
    session.add(saved)
    session.commit()
    session.refresh(saved)
    return saved


@router.put("/api/debts/{debt_id}", response_model=DebtRead)
def update_debt(debt_id: int, debt: DebtUpdate, session: Annotated[Session, Depends(get_session)]):
    result = session.execute(update(Debts).where(
        Debts.id == debt_id, Debts.current_amount <= debt.amount,
    ).values(**debt.model_dump()))
    if result.rowcount == 0:
        get_or_404(session, Debts, debt_id)
        raise HTTPException(422, "Total debt cannot be less than the amount already paid.")
    session.commit()
    return get_or_404(session, Debts, debt_id)


@router.post("/api/debts/{debt_id}/payments", response_model=DebtRead, status_code=201)
def record_debt_payment(debt_id: int, payment: DebtPaymentCreate, session: Annotated[Session, Depends(get_session)]):
    return debts.record_debt_payment(debt_id=debt_id, payment=payment, session=session)
