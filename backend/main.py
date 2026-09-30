from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, inspect, text, update, func
from sqlalchemy.orm import Session

from database import Base, engine, get_session
from models import Bills, FinancialGoal, BillPayment, Debts, DebtPayment
from schemas import BillCreate, BillRead, GoalCreate, GoalRead, GoalUpdate, GoalContribution, PaymentCreate, DebtCreate, DebtRead, DebtUpdate, DebtPaymentCreate
from decimal import Decimal
from datetime import date


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    # Add the new field to existing SQLite databases without replacing user data.
    if "is_paid" not in {column["name"] for column in inspect(engine).get_columns("bills")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE bills ADD COLUMN is_paid BOOLEAN NOT NULL DEFAULT 0"))
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/api/goals", response_model=list[GoalRead])
def list_goals(session: Annotated[Session, Depends(get_session)]):
    return session.scalars(select(FinancialGoal).order_by(FinancialGoal.id.desc())).all()


@app.post("/api/goals", response_model=GoalRead, status_code=201)
def create_goal(goal: GoalCreate, session: Annotated[Session, Depends(get_session)]):
    saved_goal = FinancialGoal(**goal.model_dump())
    session.add(saved_goal)
    session.commit()
    session.refresh(saved_goal)
    return saved_goal

@app.post("/api/bills", response_model=BillRead, status_code=201)
def create_bill(bill: BillCreate, session: Annotated[Session, Depends(get_session)]):
    saved_bill = Bills(**bill.model_dump())
    session.add(saved_bill)
    session.commit()
    session.refresh(saved_bill)
    return saved_bill

@app.get("/api/bills", response_model=list[BillRead])
def list_bills(session: Annotated[Session, Depends(get_session)]):
    return session.scalars(select(Bills).order_by(Bills.id.desc())).all()


def get_or_404(session, model, item_id):
    item = session.get(model, item_id)
    if item is None:
        raise HTTPException(404, "Item not found")
    return item


@app.put("/api/goals/{goal_id}", response_model=GoalRead)
def update_goal(goal_id: int, goal: GoalUpdate, session: Annotated[Session, Depends(get_session)]):
    saved = get_or_404(session, FinancialGoal, goal_id)
    for field, value in goal.model_dump().items():
        setattr(saved, field, value)
    session.commit()
    session.refresh(saved)
    return saved


@app.post("/api/goals/{goal_id}/contributions", response_model=GoalRead)
def add_to_goal(goal_id: int, contribution: GoalContribution, session: Annotated[Session, Depends(get_session)]):
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


@app.put("/api/bills/{bill_id}", response_model=BillRead)
def update_bill(bill_id: int, bill: BillCreate, session: Annotated[Session, Depends(get_session)]):
    saved = get_or_404(session, Bills, bill_id)
    # Scheduling a new occurrence makes it unpaid; history remains intact.
    if bill.due_date != saved.due_date:
        saved.is_paid = False
    for field, value in bill.model_dump().items():
        setattr(saved, field, value)
    session.commit()
    session.refresh(saved)
    return saved


@app.post("/api/bills/{bill_id}/payments", response_model=BillRead, status_code=201)
def record_payment(bill_id: int, payment: PaymentCreate, session: Annotated[Session, Depends(get_session)]):
    bill = get_or_404(session, Bills, bill_id)
    if bill.is_paid:
        raise HTTPException(409, "This bill is already paid. Set a new due date to record another payment.")
    if payment.paid_on > date.today():
        raise HTTPException(422, "Payment date cannot be in the future.")
    if payment.next_due_date is not None:
        if not bill.recurring:
            raise HTTPException(422, "Only recurring bills can have a next due date.")
        if payment.next_due_date <= max(payment.paid_on, bill.due_date or payment.paid_on):
            raise HTTPException(422, "Next due date must be after the payment date and current due date.")
    session.add(BillPayment(bill_id=bill.id, amount=payment.amount, paid_on=payment.paid_on, due_date=bill.due_date))
    bill.is_paid = payment.next_due_date is None
    if payment.next_due_date is not None:
        bill.due_date = payment.next_due_date
    session.commit()
    session.refresh(bill)
    return bill


@app.get("/api/debts", response_model=list[DebtRead])
def list_debts(session: Annotated[Session, Depends(get_session)]):
    return session.scalars(select(Debts).order_by(Debts.id.desc())).all()


@app.post("/api/debts", response_model=DebtRead, status_code=201)
def create_debt(debt: DebtCreate, session: Annotated[Session, Depends(get_session)]):
    saved = Debts(**debt.model_dump())
    session.add(saved)
    session.commit()
    session.refresh(saved)
    return saved


@app.put("/api/debts/{debt_id}", response_model=DebtRead)
def update_debt(debt_id: int, debt: DebtUpdate, session: Annotated[Session, Depends(get_session)]):
    result = session.execute(update(Debts).where(
        Debts.id == debt_id, Debts.current_amount <= debt.amount,
    ).values(**debt.model_dump()))
    if result.rowcount == 0:
        get_or_404(session, Debts, debt_id)
        raise HTTPException(422, "Total debt cannot be less than the amount already paid.")
    session.commit()
    return get_or_404(session, Debts, debt_id)


@app.post("/api/debts/{debt_id}/payments", response_model=DebtRead, status_code=201)
def record_debt_payment(debt_id: int, payment: DebtPaymentCreate, session: Annotated[Session, Depends(get_session)]):
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
    session.add(DebtPayment(debt_id=debt_id, amount=payment.amount, paid_on=payment.paid_on, due_date=debt.due_date))
    session.commit()
    session.refresh(debt)
    return debt


@app.get("/")
def read_root():
    return {"Hello": "Kevin"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
