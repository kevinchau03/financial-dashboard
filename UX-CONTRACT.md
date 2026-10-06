# UI contract

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Form | AppForm and AutoTextarea | frontend/src/components/AppForm.tsx | Creation, inline edit, contribution, payment, account | Build, lint, browser invalid submit |
| Date | Native date input | Existing ISO-date API fields and billStatus.ts | Optional target date, monthly bill due date, payment date | Browser field and billStatus tests |
| Select/Listbox | Native select | AccountForm.tsx | OS-owned account type popup | Sibling browser inspection |
| Scrollbar | Global CSS baseline | frontend/src/styles/budget.css | Native document and modal scrolling | Strict audit and narrow browser |
| Toast | Notice and useNotice | frontend/src/hooks/useNotice.ts | Inline three-second success overlay | Existing implementation and browser |
| CRUD | Existing feature components and DeleteItem | Backend API contracts | Create modal, inline edit, named delete confirmation | Build and existing domain tests |
| Dialog | Modal | frontend/src/components/Modal.tsx | Create, delete confirmation, discard changes | Keyboard, Escape and focus restoration |
| Unsaved changes | UnsavedChanges and form snapshots | frontend/src/unsavedForms.ts | Link navigation, inline Cancel, browser unload | Browser pending contribution navigation |
| Empty state | EmptyState | frontend/src/components/EmptyState.tsx | Goal, debt, bill starting actions | Browser empty lists |
| Statement library | StatementLibrary and StatementDetail | backend/statements.py | Paginated library, individual summary, original CSV download | Statement API tests and browser reopen/reload |

## Behavior

StatCard and DashboardPanel accept optional CardTone variants (sky, leaf, sun, rose). Tones change surfaces and typography only, with shared tokens owned by index.css and scoped rules in colors.css. Navigation, forms, loading/error states and financial calculations retain their existing behavior.

Dashboard is the default app view for an empty URL hash; explicit `#/` remains the landing page and the MyBudgetPro brand links there. The sidebar orders Dashboard, Budget, Accounts, Your Budget Wrapped. DashboardPanel owns overview section loading/error/retry states and useDashboardResource cancels superseded reads. Dashboard shows bounded account, goal, debt and bill previews, with links to their management pages. Actual recorded balances exclude planned paycheque allocations; accounts and goal savings are never combined. Bill reminders include recurring next occurrences even while the preceding occurrence is paid, and exclude paid one-time bills. Spending uses only the latest uploaded statement with its filename and date range; the summary endpoint does not fetch transaction rows. Budget owns paycheque plans, goal/debt editing and bill payments, with overview analytics moved to Dashboard. No authentication, currency, categorization or cross-statement consolidation rules are introduced.

The current React/Vite hash routes and APIs remain authoritative. Creation returns to its list and announces success. Goal updates record contributions separately from goal edits. Debt and bill payments record history without sending money. Recurring bills follow the existing monthly due-date calculation. Bills analytics sums all recorded bill amounts, so the summary label is Recorded bills.

AppForm owns validation with noValidate; native constraints remain metadata. On invalid submission, show linked textual errors and focus the first field. Require the monthly bill date before submission. Preserve data after failed saves and guard concurrent submissions. AutoTextarea owns resize-none and growth. Native date/select popup locale and geometry are intentionally OS-owned.

Modal traps focus through native showModal, restores the trigger, prevents close during a save and asks before discarding changed creation fields. DeleteItem owns irreversible deletion confirmation. Modal changes are shared with Accounts, whose visual layout remains unchanged. UnsavedChanges owns confirmation for link navigation and inline Cancel, using AppForm snapshots; browser unload uses the narrow beforeunload warning. Drafts are not persisted. Browser history traversal remains controlled by the existing hash router and is outside this link-navigation guard.

Budget lists keep their existing local disclosure state and server-returned ordering; bills additionally sort unpaid items and due dates. Load failure remains visible; summaries have Retry. Loading does not masquerade as empty data.

PaychequePlan reuses Modal and AppForm for received amount/date and optional dollar allocations to goals and unpaid debts. Its live totals use integer cents; negative remaining amounts show a textual error and submission focuses an allocated field. Partial allocation is allowed. PaychequeHistory provides paginated saved paycheques; received dates for older records remain unknown. Plans do not change actual savings or debt progress. PaychequeAllocations records an allocation as saved or paid only after confirmation with a completion date; no money is sent. Completion updates goal/debt lists and analytics without remounting their editing forms. Pending allocations can be cancelled to release their reserved amount; completed records remain in history. Deleting a target cancels its pending plans while retaining named historical entries. Requests carry stable retry keys and backend guarded writes prevent duplicate completion and over-allocation. Reads are abortable, failures retain inputs and offer retry, and saves block modal dismissal.

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

Static audit is a contract check, not runtime proof. Browser checks use existing local data and avoid changing balances or deleting records. Existing bill and planning domain tests cover calculations. Creation/save API failure and payment writes are not exercised against the user's live database during this visual redesign.
