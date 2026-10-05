# Financial goals backend

From `backend/`, install dependencies and start the API:

```powershell
uv sync
uv run uvicorn main:app --reload
```

In another terminal, from `frontend/`:

```powershell
npm install
npm run dev
```

Open the URL printed by Vite. Vite forwards `/api` to the backend on port 8000.
Goals are stored in `backend/goals.db`, created automatically on startup.
The current prototype uses a shared goal list without user accounts.

- `POST /api/goals`: create a goal with `name`, `target_amount`, `current_amount`
  (defaults to zero), optional `due_date` (`YYYY-MM-DD`), and optional `description`.
- `GET /api/goals`: list goals, newest first.

Amounts support two decimal places, with a positive target and nonnegative current
amount. Decimal values are returned as strings. Interactive API docs: `/docs`.

Run backend checks from `backend/` with `uv run pytest`.
Run frontend checks from `frontend/` with `npm run build` and `npm run lint`.

## Saved TD statements and SQL practice

Restart the backend to create the new tables in `backend/goals.db`. Uploading
through Your Budget Wrapped saves TD transactions and displays the parsed rows.
Earlier uploads must be uploaded again to save them. Generic CSV previews
(`format=csv`) are still not saved.

- `statement_imports`: `id`, `filename`, `content_hash`, `imported_at`.
- `transactions`: `id`, `statement_id`, `date`, `description`, `debit_cents`,
  `credit_cents`, `balance_cents`. Dates use `YYYY-MM-DD`; blank debits/credits
  are NULL. Amounts are integer cents (239 means $2.39).

Each file is validated before saving, and its records commit together. An
identical file, even renamed, is saved only once. Different files with overlapping
transactions are not deduplicated. All records are shared; there are no user accounts.

`get_total_spent(session)` in `analytics.py` runs this raw SQL and converts the
result from cents to a Decimal dollar amount:

```sql
SELECT COALESCE(SUM(debit_cents), 0)
FROM transactions;
```

It totals all saved debits, including transfers or fees listed as debits; credits
are not subtracted. To call it from Python, run from the backend directory:

```python
from sqlalchemy.orm import Session
from database import engine
from analytics import get_total_spent

with Session(engine) as session:
    print(get_total_spent(session))
```

## Editing and payments

- Goals are independent. Each has its own target, saved balance, optional date,
  and description. Contributions add savings directly to the selected goal.
  On startup, legacy sub-goals become standalone goals; their balances are
  deducted from their former parent's balance to preserve total savings.
  The legacy nullable parent column is cleared and retained only in old databases.
  Allocation and release APIs are removed. Monthly planning estimates remain.

- `DELETE /api/goals/{id}`, `DELETE /api/bills/{id}`, and `DELETE /api/debts/{id}`
  permanently remove an item and return 204 (404 if missing). Bill and debt
  payment histories are deleted in the same transaction. The frontend asks for
  confirmation and refreshes the corresponding summary totals.

- `PUT /api/goals/{id}` edits name, target amount, due date, and description,
  preserving the saved balance. `current_amount` is not accepted for edits.
- `POST /api/goals/{id}/contributions` accepts a positive `amount` with up to two
  decimal places and atomically adds it to the current balance, returning the updated goal.
- `PUT /api/bills/{id}` replaces editable fields using the creation payload.
  Missing IDs return 404.
- `POST /api/bills/{id}/payments` records a completed payment with `amount`,
  `paid_on` (`YYYY-MM-DD`), and optional `next_due_date` for recurring bills.
  This is recordkeeping only; no money is sent. Partial-payment balances are
  not tracked: a payment settles the current occurrence even if its amount differs.
- Bill responses include `is_paid` and `payments`, newest payment date first.
  Payments preserve the amount paid and the due date of the settled occurrence.
- Recurring bills repeat monthly and require a due date when created or edited.
  Recording a payment advances one month from the current due date, preserving
  the selected day (January 31 → February 28/29 → March 31). Late payments do
  not skip unpaid months. The next occurrence is unpaid; history records the
  settled occurrence. One-time bills are marked paid.
  The API still supports an explicit `next_due_date` override, which resets the
  monthly day. Existing bills acquire their monthly day on their next payment.
  Changing a bill's due date also schedules an unpaid occurrence and keeps history.
- Existing SQLite databases receive an additive `is_paid` column at startup;
  the payment-history table is created automatically. Existing records are preserved.

## Debts

- `GET /api/debts` and `POST /api/debts` list and create debts.
- `amount` is total debt; `current_amount` is the amount already paid (defaults to
  zero). An opening paid amount represents pre-tracking progress, not a dated payment.
- `PUT /api/debts/{id}` edits name, total amount, optional due date, description,
  and interest rate without altering payments. Total debt cannot be below paid-to-date.
- `POST /api/debts/{id}/payments` accepts `amount` and `paid_on`. It atomically
  increments paid-to-date and inserts a `DebtPayment` record with the due-date snapshot.
  Payments must be positive, no larger than the remaining balance, and not future-dated.
- Responses include `remaining_amount` and payment history ordered by payment date
  (newest first). Debts are fully paid when remaining amount is zero.
- Interest rate is informational (0–100%, two decimals); no automatic interest accrual
  or lender integration is included. New tables are created on backend startup.
