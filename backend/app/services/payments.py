"""Shared ledger writer. The calling workflow owns the transaction and balance rules."""
from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import update, select, func
from sqlalchemy.orm import Session
from app.models import Payment, Bills, Debts, FinancialGoal, Account, Paycheque, PaychequeAllocation


def add_payment(session: Session, *, kind: str, target, amount: Decimal,
                paid_on: date, source: str = 'manual', allocation_id: int | None = None,
                undo_state: dict | None = None):
    account_id = target.account_id if kind == 'goal' and source == 'paycheque' else None
    payment = Payment(kind=kind, target_name=target.name,
                      **{f'{kind}_id': target.id}, amount=amount, paid_on=paid_on,
                      due_date=target.due_date, source=source, allocation_id=allocation_id,
                      recorded_at=datetime.now(timezone.utc), undo_account_id=account_id,
                      undo_state=undo_state if undo_state is not None else {'account_deposit': account_id is not None})
    session.add(payment)
    return payment


def detach_payments(session: Session, kind: str, target_id: int):
    column = {'bill': Payment.bill_id, 'debt': Payment.debt_id, 'goal': Payment.goal_id}[kind]
    session.execute(update(Payment).where(column == target_id).values({column.key: None}))


def bill_schedule(bill: Bills) -> dict:
    return {'due_date': bill.due_date.isoformat() if bill.due_date else None,
            'is_paid': bill.is_paid, 'recurring': bill.recurring, 'recurrence_day': bill.recurrence_day}


def delete_payment(payment_id: int, session: Session):
    """Reverse a completed record once. Keep a tombstone for safe DELETE retries.

    All balance/schedule/allocation writes and the tombstone commit together.
    A no-op write serializes SQLite mutations before any reversal decisions.
    """
    try:
        found = session.execute(update(Payment).where(Payment.id == payment_id).values(amount=Payment.amount))
        if found.rowcount == 0:
            raise HTTPException(404, 'Payment not found.')
        payment = session.get(Payment, payment_id)
        session.refresh(payment)
        if payment.undone_at is not None:
            session.rollback()
            return
        if payment.undo_unavailable_reason:
            raise HTTPException(409, payment.undo_unavailable_reason)

        money = payment.amount
        allocation = session.get(PaychequeAllocation, payment.allocation_id) if payment.allocation_id else None
        if allocation is not None:
            pay = session.get(Paycheque, allocation.paycheque_id)
            if (allocation.status != 'completed' or allocation.kind != payment.kind or
                    allocation.amount != money or pay is None or pay.allocated_cents < allocation.amount_cents):
                raise HTTPException(409, 'The paycheque allocation has changed. Refresh activity before undoing.')

        if payment.kind == 'bill':
            bill = session.get(Bills, payment.bill_id)
            newer = session.scalar(select(Payment.id).where(
                Payment.bill_id == payment.bill_id, Payment.undone_at.is_(None), Payment.id > payment.id,
            ).limit(1))
            state = payment.undo_state or {}
            if newer is not None:
                raise HTTPException(409, 'Undo the most recently recorded bill payment first.')
            if bill is None or bill_schedule(bill) != state.get('after'):
                raise HTTPException(409, 'The bill schedule has changed since this payment. Undo would overwrite those changes.')
            before = state['before']
            bill.due_date = date.fromisoformat(before['due_date']) if before['due_date'] else None
            bill.is_paid = before['is_paid']
            bill.recurring = before['recurring']
            bill.recurrence_day = before['recurrence_day']
        else:
            model = Debts if payment.kind == 'debt' else FinancialGoal
            result = session.execute(update(model).where(
                model.id == payment.target_id, model.current_amount >= money,
            ).values(current_amount=func.round(model.current_amount - money, 2)))
            if result.rowcount == 0:
                raise HTTPException(409, 'This payment cannot be undone because the recorded balance is now too low or the item was deleted.')
            if payment.kind == 'goal' and (payment.undo_state or {}).get('account_deposit'):
                # Subtract only the account deposit made by the original payment,
                # even if the goal has since moved to a different account.
                account = session.get(Account, payment.undo_account_id) if payment.undo_account_id else None
                if account is None:
                    raise HTTPException(409, 'The original deposit account is no longer available.')
                assigned = session.scalar(select(func.coalesce(func.sum(FinancialGoal.current_amount), 0)).where(
                    FinancialGoal.account_id == account.id))
                changed = session.execute(update(Account).where(
                    Account.id == account.id, func.round(Account.balance - money, 2) >= assigned,
                    Account.balance >= money,
                ).values(balance=func.round(Account.balance - money, 2)))
                if changed.rowcount == 0:
                    raise HTTPException(409, 'The deposited money is no longer available in the original account. Adjust its goal assignments or balance first.')

        if allocation is not None:
            allocation.status = 'cancelled'
            allocation.completed_on = None
            session.execute(update(Paycheque).where(Paycheque.id == allocation.paycheque_id).values(
                allocated_cents=Paycheque.allocated_cents - allocation.amount_cents))
        payment.undone_at = datetime.now(timezone.utc)
        session.commit()
    except Exception:
        session.rollback()
        raise
