from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_serializer

PaymentKind = Literal['bill', 'debt', 'goal']


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: PaymentKind
    target_id: int | None
    target_name: str
    amount: Decimal
    paid_on: date
    due_date: date | None
    source: Literal['manual', 'paycheque', 'legacy']
    recorded_at: datetime | None

    @field_serializer('recorded_at')
    def serialize_recorded_at(self, value: datetime | None) -> str | None:
        # SQLite returns naive datetimes; ledger timestamps are always written in UTC.
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc).isoformat() if value.tzinfo is None else value.isoformat()


class PaymentPage(BaseModel):
    items: list[PaymentRead]
    total: int
    page: int
    page_size: int
    pages: int
