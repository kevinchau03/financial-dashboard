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

## Behavior

The current React/Vite hash routes and APIs remain authoritative. Creation returns to its list and announces success. Goal updates record contributions separately from goal edits. Debt and bill payments record history without sending money. Recurring bills follow the existing monthly due-date calculation. Bills analytics sums all recorded bill amounts, so the summary label is Recorded bills.

AppForm owns validation with noValidate; native constraints remain metadata. On invalid submission, show linked textual errors and focus the first field. Require the monthly bill date before submission. Preserve data after failed saves and guard concurrent submissions. AutoTextarea owns resize-none and growth. Native date/select popup locale and geometry are intentionally OS-owned.

Modal traps focus through native showModal, restores the trigger, prevents close during a save and asks before discarding changed creation fields. DeleteItem owns irreversible deletion confirmation. Modal changes are shared with Accounts, whose visual layout remains unchanged. UnsavedChanges owns confirmation for link navigation and inline Cancel, using AppForm snapshots; browser unload uses the narrow beforeunload warning. Drafts are not persisted. Browser history traversal remains controlled by the existing hash router and is outside this link-navigation guard.

Lists keep their existing local disclosure state and server-returned ordering; bills additionally sort unpaid items and due dates. No pagination or selection workflow is introduced. Load failure remains visible; summaries have Retry. Loading does not masquerade as empty data. Paycheque saving remains storage and display only.

## Verification boundaries

Static audit is a contract check, not runtime proof. Browser checks use existing local data and avoid changing balances or deleting records. Existing bill and planning domain tests cover calculations. Creation/save API failure and payment writes are not exercised against the user's live database during this visual redesign.
