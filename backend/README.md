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

## Editing and payments

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
- Without a next due date, a payment marks the bill paid. With a next due date,
  it schedules the next unpaid occurrence. No recurrence interval is assumed.
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
