from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import get_session
from app.models import Payment
from app.schemas.payments import PaymentKind, PaymentPage

router = APIRouter(tags=['payments'])


@router.get('/api/payments', response_model=PaymentPage)
def list_payments(session: Annotated[Session, Depends(get_session)],
                  kind: PaymentKind | None = None,
                  page: Annotated[int, Query(ge=1, le=1000000)] = 1,
                  page_size: Annotated[int, Query(ge=1, le=100)] = 20):
    query = select(Payment)
    if kind is not None:
        query = query.where(Payment.kind == kind)
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, pages)
    items = session.scalars(query.order_by(Payment.paid_on.desc(), Payment.id.desc())
                           .offset((page - 1) * page_size).limit(page_size)).all()
    return PaymentPage(items=items, total=total, page=page, page_size=page_size, pages=pages)
