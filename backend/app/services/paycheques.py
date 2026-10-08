from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
from fastapi import HTTPException
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import Paycheque, PaychequeAllocation, PaychequeAllocationBatch, FinancialGoal, Debts, DebtPayment
from app.schemas.paycheques import AllocationCreate, PaychequeCreate, AllocationBatchCreate, AllocationComplete

MAX_BALANCE = Decimal('999999999999.99')


def fingerprint(allocations: list[AllocationCreate], amount=None, received_on=None) -> str:
    entries = sorted((item.kind, item.target_id, str(item.amount.quantize(Decimal('.01')))) for item in allocations)
    return sha256(json.dumps([entries, str(amount.quantize(Decimal('.01'))) if amount is not None else None,
                              str(received_on) if received_on else None]).encode()).hexdigest()


def get_paycheque(session: Session, paycheque_id: int) -> Paycheque:
    saved = session.get(Paycheque, paycheque_id)
    if saved is None:
        raise HTTPException(404, 'Paycheque not found.')
    return saved


def reserve(session: Session, paycheque_id: int, allocations: list[AllocationCreate]):
    if len({(item.kind, item.target_id) for item in allocations}) != len(allocations):
        raise HTTPException(422, 'Use one allocation per goal or debt in this plan.')
    total = sum(int(item.amount * 100) for item in allocations)
    amount_cents = int(get_paycheque(session, paycheque_id).amount * 100)
    result = session.execute(update(Paycheque).where(
        Paycheque.id == paycheque_id,
        Paycheque.allocated_cents + total <= amount_cents,
    ).values(allocated_cents=Paycheque.allocated_cents + total))
    if result.rowcount == 0:
        get_paycheque(session, paycheque_id)
        raise HTTPException(422, 'These allocations exceed the amount left in this paycheque.')
    # The parent write serializes reservations in SQLite before checking targets.
    for item in allocations:
        model = FinancialGoal if item.kind == 'goal' else Debts
        target = session.get(model, item.target_id)
        if target is None:
            raise HTTPException(404, f'This {item.kind} no longer exists. Refresh your plan.')
        if item.kind == 'debt':
            planned = session.scalar(select(func.coalesce(func.sum(PaychequeAllocation.amount_cents), 0)).where(
                PaychequeAllocation.debt_id == target.id, PaychequeAllocation.status == 'planned',
            ))
            if Decimal(planned) / 100 + item.amount > target.remaining_amount:
                raise HTTPException(422, f'{target.name}: the planned amount exceeds the debt remaining after other allocations.')
        session.add(PaychequeAllocation(
            paycheque_id=paycheque_id, kind=item.kind, name=target.name,
            goal_id=target.id if item.kind == 'goal' else None,
            debt_id=target.id if item.kind == 'debt' else None,
            amount_cents=int(item.amount * 100),
        ))


def latest(session: Session):
    return session.scalar(select(Paycheque).order_by(Paycheque.id.desc()).limit(1))


def history(session: Session,
            offset: int = 0, limit: int = 20):
    return session.scalars(select(Paycheque).order_by(Paycheque.id.desc()).offset(offset).limit(limit)).all()


def read(paycheque_id: int, session: Session):
    return get_paycheque(session, paycheque_id)


def create(payload: PaychequeCreate, session: Session):
    if payload.received_on > date.today():
        raise HTTPException(422, 'Received date cannot be in the future.')
    key = str(payload.request_id) if payload.request_id else None
    digest = fingerprint(payload.allocations, payload.amount, payload.received_on)

    def existing_request():
        saved = session.scalar(select(Paycheque).where(Paycheque.request_id == key)) if key else None
        if saved and saved.request_fingerprint != digest:
            raise HTTPException(409, 'This paycheque was already saved with different details. Reopen it before making more allocations.')
        return saved

    existing = existing_request()
    if existing:
        return existing
    try:
        saved = Paycheque(amount=payload.amount, received_on=payload.received_on,
                         request_id=key, request_fingerprint=digest)
        session.add(saved)
        session.flush()
        reserve(session, saved.id, payload.allocations)
        session.commit()
        return get_paycheque(session, saved.id)
    except IntegrityError:
        session.rollback()
        existing = existing_request()
        if existing:
            return existing
        raise
    except Exception:
        session.rollback()
        raise


def allocate(paycheque_id: int, payload: AllocationBatchCreate, session: Session):
    try:
        # Lock the parent before checking the retry key, including concurrent retries.
        session.execute(update(Paycheque).where(Paycheque.id == paycheque_id).values(allocated_cents=Paycheque.allocated_cents))
        get_paycheque(session, paycheque_id)
        key = str(payload.request_id)
        digest = fingerprint(payload.allocations)
        prior = session.scalar(select(PaychequeAllocationBatch).where(PaychequeAllocationBatch.request_id == key))
        if prior:
            if prior.paycheque_id != paycheque_id or prior.fingerprint != digest:
                raise HTTPException(409, 'This allocation request was already saved with different details. Reopen the paycheque to review it.')
        else:
            reserve(session, paycheque_id, payload.allocations)
            session.add(PaychequeAllocationBatch(paycheque_id=paycheque_id, request_id=key, fingerprint=digest))
        session.commit()
        session.expire_all()
        return get_paycheque(session, paycheque_id)
    except Exception:
        session.rollback()
        raise


def find_allocation(session: Session, paycheque_id: int, allocation_id: int) -> PaychequeAllocation:
    allocation = session.get(PaychequeAllocation, allocation_id)
    if allocation is None or allocation.paycheque_id != paycheque_id:
        raise HTTPException(404, 'Allocation not found.')
    return allocation


def complete(paycheque_id: int, allocation_id: int, payload: AllocationComplete,
             session: Session):
    try:
        session.execute(update(Paycheque).where(Paycheque.id == paycheque_id).values(allocated_cents=Paycheque.allocated_cents))
        paycheque = get_paycheque(session, paycheque_id)
        allocation = find_allocation(session, paycheque_id, allocation_id)
        if payload.completed_on > date.today() or (paycheque.received_on and payload.completed_on < paycheque.received_on):
            raise HTTPException(422, 'Choose a completion date between the received date and today.')
        changed = session.execute(update(PaychequeAllocation).where(
            PaychequeAllocation.id == allocation.id, PaychequeAllocation.status == 'planned',
        ).values(status='completed', completed_on=payload.completed_on))
        if changed.rowcount == 0:
            if allocation.status == 'completed':
                session.rollback()
                return get_paycheque(session, paycheque_id)
            raise HTTPException(409, 'This allocation has been cancelled.')
        money = allocation.amount
        if allocation.kind == 'goal':
            result = session.execute(update(FinancialGoal).where(
                FinancialGoal.id == allocation.goal_id, FinancialGoal.current_amount <= MAX_BALANCE - money,
            ).values(current_amount=func.round(FinancialGoal.current_amount + money, 2)))
            if result.rowcount == 0:
                raise HTTPException(422, 'The goal is unavailable or this addition would exceed the supported balance. Cancel the allocation to release its money.')
        else:
            result = session.execute(update(Debts).where(
                Debts.id == allocation.debt_id,
                func.round(Debts.current_amount + money, 2) <= Debts.amount,
            ).values(current_amount=func.round(Debts.current_amount + money, 2)))
            if result.rowcount == 0:
                raise HTTPException(422, 'The debt is unavailable or the allocation exceeds its current remaining balance. Cancel it and allocate a smaller amount.')
            debt = session.get(Debts, allocation.debt_id)
            session.add(DebtPayment(debt_id=debt.id, amount=money, paid_on=payload.completed_on, due_date=debt.due_date))
        session.commit()
        return get_paycheque(session, paycheque_id)
    except Exception:
        session.rollback()
        raise


def cancel(paycheque_id: int, allocation_id: int, session: Session):
    try:
        session.execute(update(Paycheque).where(Paycheque.id == paycheque_id).values(allocated_cents=Paycheque.allocated_cents))
        allocation = find_allocation(session, paycheque_id, allocation_id)
        changed = session.execute(update(PaychequeAllocation).where(
            PaychequeAllocation.id == allocation.id, PaychequeAllocation.status == 'planned',
        ).values(status='cancelled'))
        if changed.rowcount:
            session.execute(update(Paycheque).where(Paycheque.id == paycheque_id).values(
                allocated_cents=Paycheque.allocated_cents - allocation.amount_cents))
        elif allocation.status != 'cancelled':
            raise HTTPException(409, 'Completed allocations cannot be cancelled. Their savings or payment have already been recorded.')
        session.commit()
        return get_paycheque(session, paycheque_id)
    except Exception:
        session.rollback()
        raise


def detach_target(session: Session, kind: str, target_id: int):
    """Release pending plans on deletion while retaining named allocation history."""
    column = PaychequeAllocation.goal_id if kind == 'goal' else PaychequeAllocation.debt_id
    session.execute(update(PaychequeAllocation).where(column == target_id).values(status=PaychequeAllocation.status))
    planned = session.execute(select(PaychequeAllocation.paycheque_id, func.sum(PaychequeAllocation.amount_cents)).where(
        column == target_id, PaychequeAllocation.status == 'planned',
    ).group_by(PaychequeAllocation.paycheque_id)).all()
    for paycheque_id, cents in planned:
        session.execute(update(Paycheque).where(Paycheque.id == paycheque_id).values(allocated_cents=Paycheque.allocated_cents - cents))
    session.execute(update(PaychequeAllocation).where(column == target_id, PaychequeAllocation.status == 'planned').values(status='cancelled'))
    session.execute(update(PaychequeAllocation).where(column == target_id).values({column.key: None}))
