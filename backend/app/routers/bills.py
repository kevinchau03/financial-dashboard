from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_session
from app.models import Bills
from app.services.common import get_or_404
from app.services import bills
from app.schemas.bills import BillCreate, PaymentCreate, BillRead

router = APIRouter(tags=['bills'])

@router.post("/api/bills", response_model=BillRead, status_code=201)
def create_bill(bill: BillCreate, session: Annotated[Session, Depends(get_session)]):
    if bill.recurring and bill.due_date is None:
        raise HTTPException(422, "Choose a due date for a monthly bill.")
    saved_bill = Bills(**bill.model_dump())
    saved_bill.recurrence_day = bill.due_date.day if bill.due_date else None
    session.add(saved_bill)
    session.commit()
    session.refresh(saved_bill)
    return saved_bill


@router.get("/api/bills", response_model=list[BillRead])
def list_bills(session: Annotated[Session, Depends(get_session)]):
    return session.scalars(select(Bills).order_by(Bills.id.desc())).all()


@router.delete("/api/bills/{item_id}", status_code=204)
def delete_bill(item_id: int, session: Annotated[Session, Depends(get_session)]):
    session.delete(get_or_404(session, Bills, item_id))
    session.commit()


@router.put("/api/bills/{bill_id}", response_model=BillRead)
def update_bill(bill_id: int, bill: BillCreate, session: Annotated[Session, Depends(get_session)]):
    if bill.recurring and bill.due_date is None:
        raise HTTPException(422, "Choose a due date for a monthly bill.")
    saved = get_or_404(session, Bills, bill_id)
    # Scheduling a new occurrence makes it unpaid; history remains intact.
    if bill.due_date != saved.due_date:
        saved.is_paid = False
        saved.recurrence_day = bill.due_date.day if bill.due_date else None
    for field, value in bill.model_dump().items():
        setattr(saved, field, value)
    session.commit()
    session.refresh(saved)
    return saved


@router.post("/api/bills/{bill_id}/payments", response_model=BillRead, status_code=201)
def record_payment(bill_id: int, payment: PaymentCreate, session: Annotated[Session, Depends(get_session)]):
    return bills.record_payment(bill_id=bill_id, payment=payment, session=session)
