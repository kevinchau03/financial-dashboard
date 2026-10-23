# MyBudgetPro

A personal financial planner for giving your money a purpose. Track savings goals, tackle debts, stay ahead of bills, and turn an uploaded transaction statement into **Your Budget Wrapped**.

Built with React, TypeScript, Vite, FastAPI, SQLAlchemy, pandas, and Supabase PostgreSQL/Auth. The application supports local development and separate Vercel frontend and backend deployments. V1 uses manual financial records and CSV statement uploads.

> MyBudgetPro records plans and financial activity. It does not move money, pay bills, or connect to your bank. Financial records belong to the signed-in user and are protected by API ownership checks and PostgreSQL row-level security (RLS).

## Features

### Sign-in and private records

- Visit the public landing page, then sign up or sign in with Supabase email/password authentication.
- Access only your own accounts, goals, debts, bills, paycheques, payments, and statements.
- Sign out with confirmation when there are unsaved edits.
- Reauthenticate after an API session-expiry response; drafts remain in memory for the same account.
- Supabase owns credentials and users; the application does not store passwords. Public sign-up uses Supabase.

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
- Undo eligible payments to reverse recorded balances or bill schedules. Internal undo records make retries safe; deleted targets and incomplete older records may prevent reversal.

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

### 1. Configure Supabase

Create a Supabase project and copy `backend/.env.example` to `backend/.env.local`.
Replace the placeholders with your project's settings:

```dotenv
DATABASE_URL=postgresql://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@POOLER_HOST:6543/postgres
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

Use the transaction-pooler connection string from Supabase **Connect** for Vercel.
Local development can also use the session pooler. URL-encode special characters
in the database password. Keep `.env.local` out of Git; never put the database
password or a secret/service-role key in frontend configuration.

In Supabase **Authentication → Sign In / Providers**, enable email sign-ups
to use the public Sign up form. Under **Authentication → URL Configuration**,
set the production frontend Site URL and allow each frontend callback URL, including
`http://localhost:5173/` for local development. Use the exact origin Vite prints
(for example, also allow `http://127.0.0.1:5173/` if you use that address).
Keep email confirmation enabled; registration shows a confirmation message until
a session is available. You can also create and confirm users manually under
**Authentication → Users**. Disabling new sign-ups keeps existing-user sign-in working.

See [backend/SUPABASE.md](backend/SUPABASE.md) for detailed setup, permissions,
and the access model.

### 2. Apply migrations and start the backend

```powershell
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

PostgreSQL migrations run explicitly, not during application startup. For
migrations, use an administrative session/direct connection; set
`MIGRATION_DATABASE_URL` when it differs from the runtime `DATABASE_URL`.
Migrations create empty financial tables and do not import existing SQLite records.
Use a restricted database login with permission to `SET ROLE financial_app` for
production requests. Keep administrative credentials in the migration environment.

- Health: <http://127.0.0.1:8000/api/health>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

SQLite remains available for isolated tests and local compatibility. Existing
single-user databases require an explicitly assigned owner before upgrading;
normal startup does not automatically claim their records. Back up legacy files
before any migration. Vercel requires a PostgreSQL `DATABASE_URL` and rejects the
SQLite fallback.

### 3. Start the frontend

In a second terminal, starting from the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open Vite's printed URL, normally <http://localhost:5173>, and sign in with your
Supabase user. The development proxy forwards `/api` requests to
`http://127.0.0.1:8000`. The frontend loads public Auth configuration from
`/api/auth/config`; no separate Vite Supabase environment variables are needed.

Use **Ctrl+C** in each terminal to stop its server. The backend's `--reload`
option picks up Python code changes automatically.

## Vercel deployment

The current deployment uses two projects connected to this repository:

| Setting | Frontend project | Backend project |
| --- | --- | --- |
| Root Directory | `frontend` | `backend` |
| Framework | Vite | FastAPI |
| Build Command | `npm run build` | Framework default |
| Output Directory | `dist` | Framework default |
| App entry point | `index.html` | `app/main.py` (`app`); `main.py` also re-exports it |

The backend URL configured in this repository is
<https://financial-dashboard-9qdi.vercel.app>.

### Backend environment and migrations

In the **backend project's** Vercel environment settings, add `DATABASE_URL`,
`SUPABASE_URL`, and `SUPABASE_PUBLISHABLE_KEY` for **Production**. Use the Supabase
transaction pooler for `DATABASE_URL`. Configure Preview separately, preferably
with a separate test database/project. A local `.env.local` file is not deployed
by Git and does not configure Vercel.

Apply Alembic migrations to the intended database before releasing code that
requires them. Do not run migrations from request handlers or every function
startup. After changing environment variables, create a new deployment; existing
deployments keep their previous configuration.

### Frontend API routing

`frontend/vercel.json` forwards API requests to the backend while preserving the
`/api` prefix:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://financial-dashboard-9qdi.vercel.app/api/:path*"
    }
  ]
}
```

Replace the destination if the backend production domain changes, then redeploy
the frontend. Frontend code keeps using relative `/api/...` URLs; the Vite proxy
applies only to local development. API responses are marked `Cache-Control:
no-store`; do not add CDN caching for private financial responses.

### Verify and troubleshoot

Check these paths on the backend domain, then through the frontend domain:

| Path | Expected response |
| --- | --- |
| `/api/health` | `200` with `{"status":"ok"}` |
| `/api/auth/config` | `200` with the public Supabase URL and publishable key |
| `/api/accounts`, without a bearer token | `401` |

Health confirms application startup; it does not test a database connection.
Sign in and create/read a financial record to verify the full flow. Check a second
user's account to confirm that records remain private.

- **SQLite / unable to open database file:** check the backend project's
  PostgreSQL `DATABASE_URL`, its Production scope, and redeploy. SQLite cannot be
  used as persistent storage on Vercel.
- **Sign-in unavailable:** check `SUPABASE_URL` and
  `SUPABASE_PUBLISHABLE_KEY` in the backend environment, then redeploy.
- **API returns HTML or 404 through the frontend:** check the rewrite destination
  and the frontend project's Root Directory.
- **Handler/import failure or HTTP 500:** inspect the backend deployment's runtime
  logs and confirm the deployed commit contains the latest backend changes.
- **413 during upload:** Vercel's 4.5 MB body limit includes multipart overhead.
  Responses have the same limit; large statement responses can also exceed it.

Platform references: [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi),
[environment variables](https://vercel.com/docs/environment-variables),
[rewrites](https://vercel.com/docs/routing/rewrites), and
[function limits](https://vercel.com/docs/functions/limitations).

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

- Files must be UTF-8, optionally with a BOM, and no larger than **4.5 MB (4,500,000 bytes)**.
- Empty rows are skipped. Invalid dates, amounts, descriptions, or missing required columns reject the import before transactions are saved.
- Statement amounts are stored as integer cents; monetary calculations use decimal arithmetic.
- Re-uploading an identical file reopens that user's original statement, even if the filename changes.
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

`read_csv()` uses pandas while retaining structural validation and original line numbers. `clean_data()` normalizes the four supported fields. `load_csv()` delegates statement persistence to the statement service. Analytics use SQLAlchemy ORM queries scoped to the authenticated user and selected statement. Aggregations still run in the database; UserSession blocks raw SQL so it cannot bypass the application's automatic owner filters.

Money in includes all credits, including refunds and transfers. Money out includes debits such as transfers and fees; it is not necessarily purchase spending. The most-frequent insight groups exact bank descriptions, not normalized merchants. Categories and purchased items are not inferred.

## Project structure

```text
financial-dashboard/
  backend/
    app/
      main.py                 # FastAPI application and routers
      database.py             # PostgreSQL/SQLite engines and owner-scoped sessions
      auth.py                 # Supabase token verification
      config.py               # Environment settings and production guards
      models.py               # Tables and relationships
      startup.py              # Local SQLite compatibility upgrades
      payment_migration.py    # Legacy SQLite payment migration
      routers/                # Feature API endpoints
      schemas/                # Request/response validation
      services/               # Financial workflows, CSV imports, analytics
    migrations/               # Versioned PostgreSQL schema and RLS
    alembic.ini
    SUPABASE.md               # Setup and access-model documentation
    tests/                    # Backend regression and opt-in database tests
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
    vercel.json               # Production API rewrite
  README.md
```

The landing page is available through the MyBudgetPro title. The application uses hash routes, including `#/budget`, `#/budget/paycheques`, `#/accounts`, `#/activity`, and `#/budget-wrapped`.

## Checks

Backend, from `backend/`:

```powershell
uv run pytest -q
```

The default backend tests use isolated temporary SQLite databases and mocked authentication. Live Supabase checks are opt-in and roll back their test records; see [verification instructions](backend/SUPABASE.md#verification).

Frontend, from `frontend/`:

```powershell
npm run lint
npm run build
node --experimental-strip-types --test tests/*.test.mjs
```

The frontend logic tests import TypeScript directly; the flag enables Node's built-in type stripping. `npm run build` type-checks the app and writes production assets to `frontend/dist`.

## Current boundaries and future work

- **Authentication:** public sign-up, sign-in and per-user isolation are implemented. Password resets are managed through Supabase; there is no self-service password-reset screen.
- **No bank synchronization:** balances and payments are manually recorded; statements are uploaded by the user.
- **No automatic categories yet:** a local transaction-classification model, prediction review, and category-spending insights are planned rather than implemented.
- **No automatic interest calculations:** debt interest rates are informational.
- **CSV-only v1:** current statement support is limited to the column layout documented above. PDF uploads and OCR are not included.
- **Large statements:** statement detail/upload responses currently include all parsed rows. Frontend transaction pagination does not limit response size; server-side pagination or a changed response contract is still needed for large statements on Vercel.

With the Supabase configuration, original CSV files and parsed financial data are stored in PostgreSQL. Keep backups and uploaded statements private; they can contain financial details and account identifiers. Deleting a Supabase Auth user cascades to that user's financial records.

For endpoint details, payment semantics, and database migration behavior, see [backend/README.md](backend/README.md) and the running API's `/docs` page.
