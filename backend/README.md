# MyBudgetPro backend

## Folder structure

```text
backend/
  app/
    main.py           # FastAPI setup and router registration
    startup.py        # Existing additive database compatibility upgrades
    database.py       # SQLAlchemy engine, Base and session dependency
    models.py         # Database tables and relationships
    routers/          # HTTP endpoints grouped by feature
    schemas/          # Request validation and response models by feature
    services/         # Payment/allocation rules, CSV imports and analytics
  tests/
    conftest.py        # Shared isolated database/client fixture
    test_*.py         # Feature regression tests
  main.py             # Compatibility for the old main:app launch command
  goals.db            # Existing local database; location is unchanged
  pyproject.toml
  uv.lock
```

Routers own HTTP parameters, status codes and responses. Simple CRUD remains
in the routers; multi-step financial operations live in services and retain
their existing transaction boundaries. Services share models and schemas
without importing routers. CSV parsing and loading are in
`app/services/csv_import.py`, statement persistence in
`app/services/statements.py`, and raw SQL analytics in
`app/services/analytics.py`. Shared payment response fields are defined in
`app/schemas/bills.py` and reused by debt schemas.

Run tests from `backend/` with `uv run pytest -q`. Tests use temporary databases,
not `goals.db`. Moving `database.py` into `app/` does not relocate existing data.

## Running locally

From `backend/`, install dependencies and start the API:

```powershell
uv sync
uv run uvicorn app.main:app --reload
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
The import pipeline separates extraction, cleaning and loading:

```python
extracted = read_csv(contents, format='td')
cleaned = clean_data(extracted)
table = load_csv(cleaned, session, filename=filename, contents=contents)
```

`read_csv` extracts cells and keeps the first transaction of headerless TD files.
`clean_data` skips blank rows, trims TD text, validates dates and all three amounts,
and normalizes dates/money without changing the extracted data. Invalid financial
rows reject the import rather than being silently dropped. Private date and amount
helpers keep that validation in one place.
`load_csv` maps cleaned data to recognized columns and saves TD statements through
the existing transactional storage helper. Omit the session for a table preview.
It produces the displayed four-column table:
`Date`, `Transaction`, `Debit`, `Credit`. Dates use `YYYY-MM-DD`, amounts are
two-decimal strings, and missing debits/credits are `None` (`null` in JSON).
The original parsed CSV stays unchanged. Balance remains internal storage data
and is not included in the displayed statement table.
Earlier uploads must be uploaded again to save them. Generic CSV previews
(`format=csv`) are still not saved.

- `statement_imports`: `id`, `filename`, `content_hash`, `imported_at`.
- `transactions`: `id`, `statement_id`, `date`, `description`, `debit_cents`,
  `credit_cents`, `balance_cents`. Dates use `YYYY-MM-DD`; blank debits/credits
  are NULL. Amounts are integer cents (239 means $2.39).

Each file is validated before saving, and its records commit together. An
identical file, even renamed, is saved only once. Different files with overlapping
transactions are not deduplicated. All records are shared; there are no user accounts.

`get_total_spent(session)` in `app/services/analytics.py` runs this raw SQL and converts the
result from cents to a Decimal dollar amount:

```sql
SELECT COALESCE(SUM(debit_cents), 0)
FROM transactions;
```

It totals all saved debits when no statement ID is supplied, including transfers
or fees listed as debits; credits are not subtracted. The upload endpoint passes
the uploaded file's `statement_id` to all three analytics helpers, so the frontend
shows only that statement's income, spending, and time range. Re-uploading an
existing file selects its original statement without duplicating transactions.
No combined-statement UI is implemented.

Your Budget Wrapped now includes a saved-file library. `GET /api/statements`
returns file metadata with `offset` and `limit` pagination (default 20, maximum
100). `GET /api/statements/{id}` reopens that file's four-column table and summary.
New uploads retain the original CSV bytes in `statement_imports.csv_contents`;
`GET /api/statements/{id}/file` downloads them. Backend startup adds this nullable
column to older databases without removing records. Older statements still reopen
from their transactions; re-uploading the same CSV restores its original file.

To query one statement's four columns using raw SQL:

```sql
SELECT date,
       description AS "transaction",
       debit_cents / 100.0 AS debit,
       credit_cents / 100.0 AS credit
FROM transactions
WHERE statement_id = :statement_id
ORDER BY id;
```

The existing `transactions` table owns the records; the IDs and balance column
are internal bookkeeping, so a second table with duplicate data is unnecessary.
To call the helper from Python, run from the backend directory:

```python
from sqlalchemy.orm import Session
from app.database import engine
from app.services.analytics import get_total_spent

with Session(engine) as session:
    print(get_total_spent(session, statement_id=1))
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

## Paycheque plans

The frontend Dashboard combines read-only summaries from existing account, goal,
debt and bill endpoints. `GET /api/statements/{id}/summary` returns a single saved
statement's `statement_id` and `stats` (income, spent, start/end dates) without its
transaction rows. Missing statement IDs return 404. Account and goal balances are
separate totals and statement imports are not consolidated across files.

- `POST /api/paycheques` saves `amount`, `received_on` (defaults to today), optional
  `request_id` UUID, and optional `allocations`: `{kind: "goal" | "debt", target_id,
  amount}`. Received dates cannot be future dates. Amounts use two decimal places.
- `GET /api/paycheques/latest`, `GET /api/paycheques/{id}`, and
  `GET /api/paycheques?offset=0&limit=20` return saved paycheques with allocations,
  allocated amount and remaining amount. Old paycheques retain unknown received dates.
- `POST /api/paycheques/{id}/allocations` reserves more of the remaining amount;
  requires a request UUID and at least one allocation. Unallocated income is allowed.
  Pending debt allocations across paycheques cannot exceed the outstanding debt.
- Plans do not change balances. `POST /api/paycheques/{id}/allocations/{allocation_id}/complete`
  accepts `completed_on` between receipt and today. It adds actual goal savings or
  records a debt payment atomically. Repeated completion never records money twice.
- `POST /api/paycheques/{id}/allocations/{allocation_id}/cancel` releases a pending
  allocation once. Completed entries cannot be cancelled. Deleting a target releases
  its pending allocations and retains named completed/cancelled allocation history.
- Creation and allocation UUIDs make retries idempotent; reusing a UUID with changed
  details returns 409. Guarded integer-cent reservations prevent over-allocation.
  If a debt was repaid elsewhere, completion fails without changing the plan;
  cancel that pending allocation and allocate a smaller amount.
- Startup adds the allocation tables and missing paycheque columns without clearing
  existing data. These APIs use the prototype's shared database, like existing goals.

## Paycheque accounts and deletion

Allocations accept `kind: account` with an account ID. Completing an account allocation increases its recorded balance atomically and is idempotent. It does not update a savings goal or transfer money. Do not allocate the same money to both a goal and an account. Startup adds nullable `account_id` to existing allocation tables without replacing data. `DELETE /api/paycheques/{id}` removes the paycheque, allocations and retry batches; completed goal contributions, account balances and debt payments are retained.

Account-backed goals: GoalAccountSelect reuses native select, AppForm and existing feedback. Optional links preserve older goals. Linked current_amount earmarks existing account money; direct goal additions assign existing funds and cannot exceed the account balance. Paycheque completion records a new deposit in both linked goal and account atomically. Account balance edits cannot reduce the balance below earmarked funds. Unlinking/deleting a goal releases its earmark without changing account balance. Source: backend/app/services/goals.py and backend/app/services/paycheques.py.
