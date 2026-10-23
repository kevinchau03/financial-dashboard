# UI contract

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Form | AppForm and AutoTextarea | frontend/src/components/AppForm.tsx | Creation, inline edit, contribution, payment, account | Build, lint, browser invalid submit |
| Date | Native date input | Existing ISO-date API fields and billStatus.ts | Optional target date, monthly bill due date, payment date | Browser field and billStatus tests |
| Select/Listbox | Native select | AccountForm.tsx | OS-owned account type popup | Sibling browser inspection |
| Scrollbar | Global CSS baseline | frontend/src/index.css | Native document, modal and activity table scrolling | Strict audit and narrow browser |
| Toast | Notice and useNotice | frontend/src/hooks/useNotice.ts | Inline three-second success overlay | Existing implementation and browser |
| CRUD | Existing feature components and DeleteItem | Backend API contracts | Create modal, inline edit, named delete confirmation | Build and existing domain tests |
| Dialog | Modal | frontend/src/components/Modal.tsx | Create, delete confirmation, discard changes | Keyboard, Escape and focus restoration |
| Unsaved changes | UnsavedChanges and form snapshots | frontend/src/unsavedForms.ts | Link navigation, inline Cancel, browser unload | Browser pending contribution navigation |
| Empty state | EmptyState | frontend/src/components/EmptyState.tsx | Goal, debt, bill starting actions | Browser empty lists |
| Read-only resource | useDashboardResource | Resource URL and attempt identify current data | Abort on change; 15-second timeout; explicit Retry | Loading/error/recovery browser checks |
| Authentication | AuthGate and auth.ts | backend/app/auth.py and backend/SUPABASE.md | Email/password, session recovery, sign out | Auth and ownership tests; browser sign-in flow |
| Statement library | StatementLibrary and StatementDetail | backend/statements.py | Paginated library, individual summary, original CSV download | Statement API tests and browser reopen/reload |

## Behavior

StatCard and DashboardPanel accept optional CardTone variants (sky, leaf, sun, rose). Tones identify button and highlight accents; card surfaces and ordinary typography remain neutral, with shared tokens owned by index.css and scoped rules in colors.css. Navigation, forms, loading/error states and financial calculations retain their existing behavior.

Dashboard is the default app view for an empty URL hash; explicit `#/` remains the landing page and the MyBudgetPro brand links there. The sidebar orders Dashboard, Budget (with Paycheque planner), Accounts, Activity history, Your Budget Wrapped. DashboardPanel owns overview section loading/error/retry states and useDashboardResource cancels superseded reads. Dashboard shows bounded account, goal, debt and bill previews, with links to their management pages. Actual recorded balances exclude planned paycheque allocations; accounts and goal savings are never combined. Bill reminders include recurring next occurrences even while the preceding occurrence is paid, and exclude paid one-time bills. Spending uses only the latest uploaded statement with its filename and date range; the summary endpoint does not fetch transaction rows. Budget owns paycheque plans, goal/debt editing and bill payments, with overview analytics moved to Dashboard. Currency, categorization and cross-statement consolidation rules remain unchanged. Authentication and ownership follow backend/SUPABASE.md.

The current React/Vite hash routes and APIs remain authoritative. Creation returns to its list and announces success. Goal updates record contributions separately from goal edits. Debt and bill payments record history without sending money. Recurring bills follow the existing monthly due-date calculation. Bills analytics sums all recorded bill amounts, so the summary label is Recorded bills.

AppForm owns validation with noValidate; native constraints remain metadata. On invalid submission, show linked textual errors and focus the first field. Require the monthly bill date before submission. Preserve data after failed saves and guard concurrent submissions. AutoTextarea owns resize-none and growth. Native date/select popup locale and geometry are intentionally OS-owned.

Modal traps focus through native showModal, restores the trigger, prevents close during a save and asks before discarding changed creation fields. DeleteItem owns irreversible deletion confirmation. Modal changes are shared with Accounts. UnsavedChanges owns confirmation for link navigation and inline Cancel, using AppForm snapshots; browser unload uses the narrow beforeunload warning. Drafts are not persisted. Browser history traversal remains controlled by the existing hash router and is outside this link-navigation guard.

Budget lists keep their existing local disclosure state and server-returned ordering; bills additionally sort unpaid items and due dates. Load failure remains visible; summaries have Retry. Loading does not masquerade as empty data.

PaychequePlan reuses AppForm on its dedicated Budget subpage for received amount/date and optional dollar allocations to goals and unpaid debts. Its live totals use integer cents; negative remaining amounts show a textual error and submission focuses an allocated field. Partial allocation is allowed. PaychequeHistory provides paginated saved paycheques; received dates for older records remain unknown. Plans do not change actual savings or debt progress. PaychequeAllocations records an allocation as saved or paid only after confirmation with a completion date; no money is sent. Completion updates goal/debt lists and analytics without remounting their editing forms. Pending allocations can be cancelled to release their reserved amount; completed records remain in history. Deleting a target cancels its pending plans while retaining named historical entries. Requests carry stable retry keys and backend guarded writes prevent duplicate completion and over-allocation. Reads are abortable, failures retain inputs and offer retry, and saves block navigation or draft cancellation.

Your Budget Wrapped lists saved files newest first, 20 per server page. Selecting
a file sets `#/budget-wrapped?statement=id`, so refresh and browser history reopen
that statement. The summary and transaction rows always use that ID.
The shared useHash subscription reads the current URL directly; routing.ts owns
page-path normalization and statement parameter parsing so neither is stored as
stale component state.
Table pages show 50 rows at a time. Library and detail reads cancel superseded requests and
offer Retry. Upload success opens the saved statement; identical files reuse their
original record. New files retain original bytes for download. Older records remain
readable; re-uploading their CSV restores original-file download. Storage is the
prototype's existing shared database, with no authentication changes. Filename and
CSV contents are treated as data and never rendered as HTML. Native file selection
remains owned by CsvUpload with the existing 5 MB CSV validation.

## Verification boundaries

Static audit is a contract check, not runtime proof. Activity browser checks use a disposable database and cover a contribution recorded through Budget, filtering, pagination, loading, empty states, connection failure and Retry, keyboard focus, and desktop/narrow layouts. They do not change the user's saved financial data. Backend tests cover migration, rollback, balances, concurrency and retention.

Paycheque allocation now includes accounts using the existing grouped numeric fields and record dialog. Account deposits update recorded balances only when completed; linked goal deposits update the account and earmarked goal together; each dollar is allocated once. Paycheque deletion uses DeleteItem confirmation, removing its plans/history while preserving completed savings, balances and payments. Policy source: backend/app/services/paycheques.py.

Account-backed goals: GoalAccountSelect reuses native select, AppForm and existing feedback. Optional links preserve older goals. Linked current_amount earmarks existing account money; direct goal additions assign existing funds and cannot exceed the account balance. Paycheque completion records a new deposit in both linked goal and account atomically. Account balance edits cannot reduce the balance below earmarked funds. Unlinking/deleting a goal releases its earmark without changing account balance. Source: backend/app/services/goals.py and backend/app/services/paycheques.py.

Goal card summaries show the linked account, or No linked account, without expansion. Paid-off debts reuse DeleteItem with a Resolve debt variant and explicit confirmation that recorded payments remain in Activity history. The backend rechecks zero remaining balance before resolution. Source: backend/app/routers/debts.py.

CollapsibleItem supports an optional cardAction outside the details disclosure. Paid-off debts show Resolve debt there even while collapsed, with the same DeleteItem confirmation and backend balance guard.

Dashboard unboxed totals reuse StatCard and the existing abortable resources. Total saved sums goal current amounts without adding account balances; Total debt sums remaining balances; Total bills sums all recorded bill amounts including paid bills and is explicitly not a monthly projection. Summary totals use four columns on wide screens and two on narrower screens.

Accounts balance edits use AccountRow and AppForm in a full-width divided list. Clicking the balance focuses/selects the numeric field; Enter or Save submits the existing PUT account endpoint with name/type preserved. The returned balance, earmarked amount and unassigned amount replace the row together, and Notice announces success. Failed saves keep the draft and textual server error. Duplicate submissions and cancellation during saves are blocked. Cancel and Escape invoke the existing unsaved-change confirmation when dirty, restoring focus to the balance trigger after closing. Account details and creation retain AccountForm/Modal. Policy source: backend/app/routers/accounts.py; linked-goal funds cannot exceed the recorded balance.

Paycheque planner lives at #/budget/paycheques as an indented Budget navigation child. PaychequePlan owns the guided page worksheet using AppForm, native date inputs and existing account/goal/debt targets; PaychequeAllocations, PaychequeHistory and DeleteItem retain recording, history and deletion behavior. Received money, bills/everyday reserves and allocations are saved atomically. Reserves reduce remaining money but never update bills or balances. Desktop uses a sticky review panel; narrow screens show a sticky remaining amount above the worksheet. Save stays on the page with the actual saved plan. No automatic financial recommendations are made. Reserves are fixed for a saved paycheque; cancelled pending allocations release only their allocation amounts.

StatementDetail first offers an optional six-screen Budget Wrapped using StatementWrapped; skip, exit, finish and replay retain the statement summary and table. Each screen is manually advanced with Back/Next or six accessible progress buttons, with heading focus on change, shared currency/date formatting, reduced-motion support and scoped accent tokens. Insights load from the selected statement /insights endpoint with abort, retry and exit recovery. Money in/out include transfers; exact descriptions are not merchant or item classifications; largest movement includes either debit or credit; highest spending excludes nonpositive debit days and ties use earliest date.

Wrapped insight details: the largest transaction returns amount, debit/credit kind, description and date, with deterministic ties. The highest-spending day returns its positive-debit total and all same-statement transactions on that date. The final slide shows a separate debit/credit table, ten rows per page, including credits without deducting them from spending. Existing table/scroll styles, currency formatting and controls are reused.

Dashboard uses an open ledger layout: four unboxed totals, divided account/bill lists, borderless goal/debt progress sections, and one neutral latest-statement surface. Copy is concise; goal/account overlap and recorded-bill scope remain explicit. The main action opens the paycheque planner. Existing resources, bounded previews, retries and financial calculations are unchanged. overview.css owns dashboard layout and container breakpoints (1000/640/420px), reusing index.css tokens and Noto Sans.

Dashboard hierarchy: goal/debt progress leads the main column with larger headings and thicker progress tracks. Latest statement sits at upper right with a sky-filled “View Your Budget Wrapped” link to that statement. Accounts and a compact three-bill preview follow below. Below 680px the reading order is progress, statement, accounts, bills; progress columns stack below 440px. Existing totals and retries remain.

## Activity history

Personal budgeting records for the prototype's single shared workspace. English copy, CAD amounts and browser locale formatting. Payment dates are calendar dates; recording timestamps are stored in UTC and displayed with the local timezone. No financial institution integration or money movement. Accessibility target: WCAG 2.2 AA.

### Business-context sources

| Domain | Source | Reviewed |
|---|---|---|
| Shared data and permissions | backend/README.md: all records are shared; no user accounts | 2026-10-20 |
| Payment lifecycle, migration and retention | backend/README.md: Unified payment ledger | 2026-10-20 |
| Balance constraints and atomic updates | backend/app/services/debts.py, backend/app/services/goals.py, backend/app/services/paycheques.py | 2026-10-20 |
| Visual identity and market/content conventions | DESIGN.md | 2026-10-20 |

### Dataset navigation

Activity uses GET /api/payments, 20 records per page, descending payment date then descending ID. Kind and page persist in the hash query. Changing kind resets to page one. The server clamps pages after data changes. Browser Back restores the previous filter/page. Counts describe the filtered dataset. Empty and failed results have distinct text and a recovery action; loading reserves a minimum result area. History scrolls horizontally inside its named keyboard-focusable region on narrow screens; document scrolling remains natural. Full names wrap and amounts remain readable.

### Activity flow ledger

| Operation | Pending | Success | Failure recovery | Source |
|---|---|---|---|---|
| Record payment/contribution | Shared form disables duplicate activation | Update owner and show its existing notice; Activity reads committed ledger | Keep values and inline error | Payment/contribution endpoints; DESIGN.md |
| Complete allocation | Wait for server; no optimistic financial update | Balance and one payment saved together | Keep pending allocation; explicit retry | backend/app/services/paycheques.py |
| Delete target / resolve debt | DeleteItem + Modal confirmation | Remove target; retain named activity | Keep dialog and inline error | backend/README.md: Unified payment ledger |
| Filter/page activity | Abort old request; announce loading | Render matching page and range; page changes focus ledger heading | Persistent alert and Retry | backend/app/routers/payments.py |

Routes use usePage for document titles and main focus. Activity filters are navigation links with current state; pagination uses labelled buttons and a live range. Existing Modal owns focus trap, Escape and restoration; Notice owns transient feedback. Shared CSS owns focus, hover, pressed, disabled, reduced motion and global scrollbars.

Dashboard simplification: three recorded totals (accounts, saved toward goals, remaining debt), one conditional next-payment/overdue reminder, and three-item goal/debt previews. Unfinished goals lead via a stable copied sort; completed goals remain in the full view. Statement and compact bills share a right rail; accounts are a supporting two-column list. Mobile stacks naturally with account total leading. Recorded bills aggregate is removed from this overview to avoid competing with date-specific reminders; Budget remains its owner. Existing resources, error/retry and money semantics are preserved.

Budget Wrapped now opens saved files directly into their summary instead of an invitation gate. Play Budget Wrapped retains the existing optional six-screen experience and summary return/focus. The library is an open list with latest-upload label and a supporting upload panel; CSV format guidance is disclosed on request. Summary shows money in, money out and net movement (credits minus debits using sumAmounts), explicitly file-scoped and not savings. Review transactions focuses and scrolls to the table heading without changing the route. Existing uploads, 20-file/50-row paging, original-file downloads, abort/retry, and backend insights remain. statements.css owns layout at container widths 760/480px using shared tokens.


### Undo payment

Source: backend/README.md, Undo a payment; backend/app/services/payments.py.
UndoPayment owns the visible labelled arrow button and reuses Modal plus the shared
notice system. Confirm the named target, amount and payment date before DELETE.
Pending blocks repeat submit and modal close; failure retains the confirmation
and server explanation. An uncertain network result permits an idempotent retry.
Success removes the active record after server acknowledgement, refetches the
filtered page, preserves its URL state and moves focus to the ledger heading.
The server clamps a now-empty last page. Missing targets and incomplete historic
undo context have disabled actions with visible reasons. Schedule/balance conflicts
remain server-owned and return 409 without partial changes. Undo sends no money.


Authentication: the entire financial app is gated until Supabase has supplied a
session. The API independently verifies every access token and scopes every
financial query to that user. auth.ts is the only owner for API requests and
session expiry; it attaches bearer tokens only to relative /api/ paths. Original
CSV downloads use this same authenticated request path. Tokens are managed by the
official SDK in sessionStorage, scoped to the current tab; passwords are never
stored. The same-account reauthentication panel hides and makes mounted content
inert while retaining drafts in memory. An account change remounts all financial
screens, and explicit sign-out clears them. Sign out uses the existing unsaved
changes confirmation. Login failure preserves email and clears the password.
The landing page (including an empty URL) is public regardless of authentication
configuration or session loading. Sign in and Sign up are public credential flows
owned by AuthGate and AppForm. Registration uses Supabase signUp, a 12-character
minimum, generic errors, duplicate-submit prevention and email-confirmation feedback.
Immediate sessions open Dashboard; email confirmation can establish a session through
the SDK PKCE callback, or users can return and sign in. Protected deep links remain
intact during sign-in. Password resets remain handled by the app owner in Supabase.
Source: current public-landing/sign-up request; backend/SUPABASE.md.

AppForm accepts an optional feedback slot and reserved validation space for sign-in. Validation and server errors share one inline region so credential failures and invalid submissions do not move the submit button. Other forms retain their existing layout.
