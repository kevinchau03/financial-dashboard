from datetime import date
from fastapi import HTTPException
from sqlalchemy import update, func
from sqlalchemy.orm import Session
from app.models import Debts
from app.services.payments import add_payment
from app.services.common import get_or_404
from app.schemas.debts import DebtPaymentCreate

def record_debt_payment(debt_id: int, payment: DebtPaymentCreate, session: Session):
    if payment.paid_on > date.today():
        raise HTTPException(422, "Payment date cannot be in the future.")
    # The guarded increment and payment record commit together. Round SQLite's
    # numeric arithmetic to cents so an exact final payment is accepted.
    result = session.execute(update(Debts).where(
        Debts.id == debt_id,
        func.round(Debts.current_amount + payment.amount, 2) <= Debts.amount,
    ).values(current_amount=func.round(Debts.current_amount + payment.amount, 2)))
    if result.rowcount == 0:
        get_or_404(session, Debts, debt_id)
        raise HTTPException(422, "Payment cannot exceed the remaining debt balance.")
    debt = get_or_404(session, Debts, debt_id)
    add_payment(session, kind='debt', target=debt, amount=payment.amount, paid_on=payment.paid_on)
    session.commit()
    session.refresh(debt)
    return debt
