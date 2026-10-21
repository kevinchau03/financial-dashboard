# MyBudgetPro

A personal financial planner for giving your money a purpose. Track savings goals, tackle debts, stay ahead of bills, and turn an uploaded transaction statement into **Your Budget Wrapped**.

Built with React, TypeScript, Vite, FastAPI, SQLAlchemy, pandas, and SQLite. The current version runs locally and uses manual financial records and CSV uploads.

> MyBudgetPro records plans and financial activity. It does not move money, pay bills, or connect to your bank. This is currently a shared-data prototype without user authentication or per-user data isolation.

## Features

### Dashboard

- View account balances, total saved toward goals, remaining debt, and recorded bill totals.
- See previews of accounts, goals, debts, upcoming bills, and the latest uploaded statement.
- Account balances and goal savings are separate totals, so earmarked savings are not added twice.

### Budget

- Create, edit, and delete savings goals, debts, and bills.
- Add savings without changing a goal's name, target, or other details.
- Link a goal to an account and earmark part of that account's balance.
- Record debt payments and resolve fully paid debts.
- Track bill payments and monthly recurring due dates.
- Expand individual items to see details and payment history.

### Paycheque planner

A dedicated subpage under Budget guides you through:

1. Entering take-home pay and the date received, with an optional next payday.
2. Reserving money for bills and everyday spending.
3. Allocating the remainder toward goals, debts, or accounts.
4. Reviewing and saving the plan.

Live totals help prevent over-allocation. You can reuse previous paycheque amounts, leave money unallocated, review history, and cancel pending allocations. Saving a plan does not update actual balances; recording an allocation as completed does.

For linked goals, completing a paycheque allocation updates the goal and its account together. Do not allocate the same deposit to both destinations. Deleting a paycheque preserves completed financial activity.

### Accounts

- Record accounts such as chequing, savings, TFSA, and FHSA accounts.
- Update balances manually.
- See linked goals, earmarked funds, and unassigned money.

### Activity history

- Browse completed goal contributions, debt payments, and bill payments in one ledger.
- Filter by activity type and navigate paginated results.
- See payment dates, saved target names, and whether an entry came from direct input or a paycheque allocation.
- Payment records remain available when a goal, debt, bill, or paycheque is deleted.

### Your Budget Wrapped

- Upload a supported bank CSV and save it in a statement library.
- Reopen individual statements and download retained original files.
- Choose a normal summary or an optional six-screen recap showing:
  1. Money in.
  2. Money out.
  3. Transaction count.
  4. Most frequent exact transaction description and its occurrence count.
  5. Largest transaction, including debit/credit direction, description, and date.
  6. Highest-spending day, its total, and the transactions on that date.
- Move backward, skip to the summary, or replay the recap.

All statement analytics require a statement ID. Separate uploads are not combined into one recap.

## Local setup

### Requirements

- Python **3.12 or newer**.
- [uv](https://docs.astral.sh/uv/) for backend dependencies.
- Node.js **22.12 or newer** and npm. The installed Vite version also supports Node 20.19.x and compatible later 20.x releases.

Run the backend and frontend in separate terminals. The commands below assume you start in the repository root.

### 1. Start the backend

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: <http://127.0.0.1:8000>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

The SQLite database is created automatically at `backend/goals.db`. No database server or API key is needed for the current features. Startup also applies the project's existing database upgrades.

**Upgrading an existing database:** stop older backend processes and back up `backend/goals.db` before starting the updated app. The unified-payment migration moves legacy payment records into the shared ledger and retires the old payment tables. See the [backend documentation](backend/README.md#unified-payment-ledger) for details.

### 2. Start the frontend

In a second terminal, starting from the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite, normally <http://localhost:5173>. Its development proxy forwards `/api` requests to `http://127.0.0.1:8000`.

Use **Ctrl+C** in each terminal to stop its server. The backend's `--reload` option picks up Python code changes automatically.

## CSV import format

The statement upload currently supports **headerless TD/CIBC-style files** with these first four columns:

| Position | Field | Accepted value |
| --- | --- | --- |
| 1 | Date | `MM/DD/YYYY` or `YYYY-MM-DD` |
| 2 | Transaction name | Non-empty description; quote text containing commas |
| 3 | Debit | Money out, with up to two decimal places; blank when absent |
| 4 | Credit | Money in, with up to two decimal places; blank when absent |

Additional columns, such as an account number or balance, are ignored when building transaction records. They remain in the retained original CSV file.

Example without a header row:

```csv
2026-10-01,"Coffee shop, Toronto",4.50,,extra bank metadata
2026-10-02,Payroll,,2000.00,extra bank metadata
```

- Files must be UTF-8, optionally with a BOM, and no larger than **5 MB**.
- Empty rows are skipped. Invalid dates, amounts, descriptions, or missing required columns reject the import before transactions are saved.
- Statement amounts are stored as integer cents; monetary calculations use decimal arithmetic.
- Re-uploading an identical file reopens the original statement, even if the filename changes.
- Different files with overlapping transactions are **not** deduplicated against each other.
- Other banks, header layouts, signed single-amount columns, and reordered columns are not automatically supported.

The API retains `format=td` for this bank-statement import path. The separate `format=csv` path previews generic header-based CSVs without saving them as statements.

### How imports and analytics work

```text
CSV bytes -> read_csv() -> clean_data() -> load_csv()
                                            |
                                            v
                               Statement + transactions
                                            |
                                            v
                               SQL analytics for that statement
                                            |
                                            v
                               Summary and Wrapped screens
```

`read_csv()` uses pandas while retaining structural validation and original line numbers. `clean_data()` normalizes the four supported fields. `load_csv()` delegates statement persistence to the statement service. Analytics use parameterized SQL scoped to one statement.

Money in includes all credits, including refunds and transfers. Money out includes debits such as transfers and fees; it is not necessarily purchase spending. The most-frequent insight groups exact bank descriptions, not normalized merchants. Categories and purchased items are not inferred.

## Project structure

```text
financial-dashboard/
  backend/
    app/
      main.py                 # FastAPI application and routers
      database.py             # SQLite engine and session dependency
      models.py               # Tables and relationships
      startup.py              # Database initialization and upgrades
      payment_migration.py    # Unified payment ledger migration
      routers/                # Feature API endpoints
      schemas/                # Request/response validation
      services/               # Financial workflows, CSV imports, analytics
    tests/                    # Backend regression tests
    pyproject.toml
    uv.lock
  frontend/
    src/
      App.tsx                 # Application shell and hash-based routing
      pages/                  # Dashboard, Budget, Accounts, Activity, Wrapped
      components/             # Feature components and shared UI
      hooks/                  # Navigation, resource loading, notices
      styles/                 # Feature styles
    tests/                    # Node-based tests for frontend logic
    package.json
    package-lock.json
  README.md
```

The landing page is available through the MyBudgetPro title. The application uses hash routes, including `#/budget`, `#/budget/paycheques`, `#/accounts`, `#/activity`, and `#/budget-wrapped`.

## Checks

Backend, from `backend/`:

```powershell
uv run pytest -q
```

Backend tests use isolated temporary databases rather than your local `goals.db`.

Frontend, from `frontend/`:

```powershell
npm run lint
npm run build
node --experimental-strip-types --test tests/*.test.mjs
```

The frontend logic tests import TypeScript directly; the flag enables Node's built-in type stripping. `npm run build` type-checks the app and writes production assets to `frontend/dist`.

## Current boundaries and future work

- **No user accounts:** all records share one local database. Authentication and ownership checks are needed before hosting private financial data for multiple users.
- **No bank synchronization:** balances and payments are manually recorded; statements are uploaded by the user.
- **No automatic categories yet:** a local transaction-classification model, prediction review, and category-spending insights are planned rather than implemented.
- **No automatic interest calculations:** debt interest rates are informational.
- **No universal bank importer:** current statement support is limited to the column layout documented above.
- **Local development configuration:** production hosting needs persistent storage, backups, HTTPS, and production frontend/API routing. Vite's development proxy is not a production configuration.

The original statement files and parsed financial data are stored locally in SQLite. Keep database backups and uploaded statements private; they can contain financial details and account identifiers.

For endpoint details, payment semantics, and database migration behavior, see [backend/README.md](backend/README.md) and the running API's `/docs` page.
