from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_session
from app.schemas.paycheques import PaychequeCreate, PaychequeRead, AllocationBatchCreate, AllocationComplete
from app.services import paycheques

router = APIRouter(prefix='/api/paycheques', tags=['paycheques'])

@router.get('/latest', response_model=PaychequeRead | None)
def latest(session: Annotated[Session, Depends(get_session)]):
    return paycheques.latest(session=session)


@router.get('', response_model=list[PaychequeRead])
def history(session: Annotated[Session, Depends(get_session)],
            offset: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return paycheques.history(session=session, offset=offset, limit=limit)


@router.get('/{paycheque_id}', response_model=PaychequeRead)
def read(paycheque_id: int, session: Annotated[Session, Depends(get_session)]):
    return paycheques.read(paycheque_id=paycheque_id, session=session)


@router.post('', response_model=PaychequeRead, status_code=201)
def create(payload: PaychequeCreate, session: Annotated[Session, Depends(get_session)]):
    return paycheques.create(payload=payload, session=session)


@router.post('/{paycheque_id}/allocations', response_model=PaychequeRead)
def allocate(paycheque_id: int, payload: AllocationBatchCreate, session: Annotated[Session, Depends(get_session)]):
    return paycheques.allocate(paycheque_id=paycheque_id, payload=payload, session=session)


@router.post('/{paycheque_id}/allocations/{allocation_id}/complete', response_model=PaychequeRead)
def complete(paycheque_id: int, allocation_id: int, payload: AllocationComplete,
             session: Annotated[Session, Depends(get_session)]):
    return paycheques.complete(paycheque_id=paycheque_id, allocation_id=allocation_id, payload=payload, session=session)


@router.post('/{paycheque_id}/allocations/{allocation_id}/cancel', response_model=PaychequeRead)
def cancel(paycheque_id: int, allocation_id: int, session: Annotated[Session, Depends(get_session)]):
    return paycheques.cancel(paycheque_id=paycheque_id, allocation_id=allocation_id, session=session)


@router.delete('/{paycheque_id}', status_code=204)
def delete_paycheque(paycheque_id: int, session: Annotated[Session, Depends(get_session)]):
    paycheques.remove(paycheque_id, session)
