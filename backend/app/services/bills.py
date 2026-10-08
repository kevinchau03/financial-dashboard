from datetime import date
from calendar import monthrange
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Bills, BillPayment
from app.services.common import get_or_404
from app.schemas.bills import PaymentCreate

def record_payment(bill_id: int, payment: PaymentCreate, session: Session):
    bill = get_or_404(session, Bills, bill_id)
    if bill.is_paid:
        raise HTTPException(409, "This bill is already paid. Set a new due date to record another payment.")
    if payment.paid_on > date.today():
        raise HTTPException(422, "Payment date cannot be in the future.")
    next_due_date = payment.next_due_date
    if bill.recurring and next_due_date is None:
        if bill.due_date is None:
            raise HTTPException(422, "Set a due date before recording a recurring bill payment.")
        year = bill.due_date.year + (bill.due_date.month == 12)
        month = bill.due_date.month % 12 + 1
        if year > 9999:
            raise HTTPException(422, "The next due date is outside the supported date range.")
        bill.recurrence_day = bill.recurrence_day or bill.due_date.day
        next_due_date = date(year, month, min(bill.recurrence_day, monthrange(year, month)[1]))
    if payment.next_due_date is not None:
        if not bill.recurring:
            raise HTTPException(422, "Only recurring bills can have a next due date.")
        if payment.next_due_date <= max(payment.paid_on, bill.due_date or payment.paid_on):
            raise HTTPException(422, "Next due date must be after the payment date and current due date.")
    session.add(BillPayment(bill_id=bill.id, amount=payment.amount, paid_on=payment.paid_on, due_date=bill.due_date))
    bill.is_paid = next_due_date is None
    if next_due_date is not None:
        if payment.next_due_date is not None:
            bill.recurrence_day = next_due_date.day
        bill.due_date = next_due_date
    session.commit()
    session.refresh(bill)
    return bill
