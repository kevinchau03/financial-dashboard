# Local Supabase setup

The React app signs in through Supabase Auth. FastAPI verifies each bearer token
with Supabase's `/auth/v1/user` endpoint, then runs financial queries for that
verified UUID. Supabase owns passwords and `auth.users`; no duplicate user or
password model is needed. The first migration creates empty financial tables.
It does not import, delete, or modify `backend/goals.db`.

## 1. Local configuration

In the Supabase project, open **Connect** to find the project URL and publishable
key. The key is also under **Settings → API Keys**. Put these in
`backend/.env.local` (ignored by Git):

```dotenv
DATABASE_URL=postgresql://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@POOLER_HOST:5432/postgres
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

Copy the actual connection string from **Connect → Session pooler** for local
development. URL-encode special characters in the database password. The database
connection uses TLS and the psycopg driver. Keep this password on the backend.
Never use a secret/service-role key as the publishable key; the configuration
endpoint explicitly rejects it. Frontend configuration comes from
`/api/auth/config`, so no duplicated Vite environment variables are required.
Environment variables set by the host take precedence over `.env.local`.

## 2. Create a user

Under **Authentication → Users → Add user**, create an email/password user and
confirm the email for local testing. Disable public sign-ups in Auth settings if
this is a private app. The application includes a public landing page and sign-up
screen; enable email sign-ups to use registration. Set the frontend Site URL under
Authentication → URL Configuration and allow the frontend callback URLs, including
`http://localhost:5173/` for local development (or `http://127.0.0.1:5173/` when used).
Keep email confirmation enabled. The SDK uses PKCE; a confirmation link opened in
another tab may require signing in manually afterward because session storage is
scoped to a tab. Password resets are managed by the app owner in Supabase for now.
Do not share user passwords or database credentials in chat.

## 3. Apply the schema

From `backend/`:

```powershell
uv sync
uv run alembic upgrade head
uv run alembic current
```

Run migrations explicitly before starting the API. PostgreSQL startup does not
create or alter tables. The migration is transactional and serialized with an
advisory lock; rerunning `upgrade head` is safe. It targets a fresh database and
does not overwrite pre-existing financial tables. Downgrading intentionally
refuses to drop financial data; use a verified backup for recovery.

If migration and runtime credentials differ, set `MIGRATION_DATABASE_URL` to the
administrative session/direct connection. It takes precedence for Alembic only.
The migration account needs permission to create tables, roles and Auth foreign
keys. Runtime connections must be permitted to `SET ROLE financial_app`.
Future migrations can use `alembic revision --autogenerate -m "description"`.
The migration environment preserves PostgreSQL-only ownership constraints during
autogeneration. Review every new table for required ownership, Auth and composite
foreign keys, restricted grants, and RLS; Alembic does not generate policies.

## 4. Start the app

From `backend/`: `uv run uvicorn app.main:app --reload`.
From `frontend/`: `npm ci`, then `npm run dev`.
Open Vite's URL and sign in with the user created in step 2.

Start with empty lists, create an account/goal, record a contribution, then check
Activity history and undo it. Sign out and sign in with a second account; its
lists must be empty. CSV downloads also require a signed-in session.

## Access model

- Every financial table has an indexed, required `user_id` foreign key to
  `auth.users`. The database enforces same-owner links between records.
- FastAPI gets the owner exclusively from the verified Supabase identity. Owner
  fields are absent from request schemas. `UserSession` filters ORM reads,
  updates, deletes, counts, aggregates, relationships, and retry lookups. It
  rejects raw SQL, bulk inserts, ownership changes and cross-owner references.
- Each PostgreSQL transaction switches to the restricted `financial_app` role
  and sets a transaction-local owner. RLS has both `USING` and `WITH CHECK`.
  An unset owner sees no rows. Pooled connections cannot retain the identity
  after the transaction ends.
- Browser `anon` and `authenticated` roles have no direct access to financial
  tables or sequences. All financial mutations pass through FastAPI so direct
  Data API writes cannot bypass payment and allocation rules.
- The supplied connection can use the local Supabase administrator login;
  requests still switch into the restricted role. Before production, use a
  separate login with only membership in `financial_app`, no table ownership,
  no `BYPASSRLS`, and no administrative privileges. Keep administrative credentials
  exclusively in the migration environment.
- Supabase manages access/refresh tokens in per-tab `sessionStorage`; passwords
  and financial drafts are never persisted by this app. Explicit sign-out clears
  the current tab's session. Already issued bearer tokens remain valid until
  Supabase rejects them or they expire; use appropriate Auth session settings.
- API responses use `Cache-Control: no-store`. Authentication failures return
  401, provider/configuration outages return 503, and unavailable foreign records
  return 404 without revealing their owner.
- Deleting an Auth user cascades to that user's financial records. Back up any
  records you need before deleting a user in Supabase.

## Verification

```powershell
# Isolated SQLite tests, including token verification and two-user isolation
uv run pytest -q

# Optional live PostgreSQL checks (temporary rows, rolled back on completion)
$env:RUN_SUPABASE_TESTS = '1'
uv run pytest tests/test_supabase_integration.py -q
Remove-Item Env:RUN_SUPABASE_TESTS
```

The integration checks require the administrative database connection. They do
not use real passwords, send email or retain test users or financial records.
Vercel hosting and deployment configuration are separate from this local setup.
For a later serverless deployment use Supabase's transaction pooler; prepared
statements are already disabled and SQLAlchemy delegates pooling to Supavisor.

References: [Supabase connection methods](https://supabase.com/docs/guides/database/connecting-to-postgres),
[Auth user verification](https://supabase.com/docs/reference/javascript/auth-getuser),
[RLS](https://supabase.com/docs/guides/database/postgres/row-level-security).
