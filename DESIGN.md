---
version: alpha
name: MyBudgetPro
description: A Warm Gouache personal budget workspace in cream, dusty blue and meadow green.
colors:
  primary: "#adc69a"
  background: "#19262e"
  surface: "#24343b"
  text: "#edf0e8"
  muted: "#b3c3bf"
  wash: "#24343b"
  border: "#5e777a"
  focus: "#a3c7dc"
  danger: "#e1a18a"
  leaf-accent: "#adc69a"
  leaf-surface: "#24343b"
  sky-accent: "#a3c7dc"
  sky-surface: "#24343b"
  sun-accent: "#e0bb78"
  sun-surface: "#24343b"
  rose-accent: "#d6a6b5"
  rose-surface: "#24343b"
typography:
  sans:
    fontFamily: "Noto Sans, system-ui, sans-serif"
  display:
    fontFamily: "Noto Sans, system-ui, sans-serif"
rounded:
  DEFAULT: "12px"
  control: "7px"
spacing:
  section-gap: "28px"
  card-padding: "16px"
components:
  button: { backgroundColor: "{colors.primary}", textColor: "#19262e" }
  card: { backgroundColor: "{colors.surface}", textColor: "{colors.text}" }
  dialog: { backgroundColor: "{colors.surface}", textColor: "{colors.text}" }
  guidance: { backgroundColor: "{colors.wash}", textColor: "{colors.muted}" }
  divider: { backgroundColor: "{colors.border}" }
  focus-ring: { backgroundColor: "{colors.focus}" }
  error-text: { textColor: "{colors.danger}" }
  savings-card: { backgroundColor: "{colors.surface}", textColor: "{colors.text}" }
  accounts-card: { backgroundColor: "{colors.surface}", textColor: "{colors.text}" }
  bills-card: { backgroundColor: "{colors.surface}", textColor: "{colors.text}" }
  debt-card: { backgroundColor: "{colors.surface}", textColor: "{colors.text}" }
---

Paycheque planning uses the shared dark surfaces and earthy action accents. Keep entry compact, use a dedicated Budget subpage for the allocation worksheet, show three calm numeric totals and group targets into goals, debts and accounts. Use explicit Planned and Recorded labels instead of showing projected progress as actual savings. History stays behind a button and allocation details are collapsible. Reuse the shared form, dialog, notice, focus and scrollbar patterns; retain native date selection. Narrow screens keep amount fields readable without horizontal overflow.

# MyBudgetPro Design System

Dashboard key totals use three matching neutral cards: shared surface, border, 12px corners and 20px padding. Other dashboard sections retain their open layout. The responsive summary grid is preserved. Runtime owner: `frontend/src/styles/overview.css`.

## Overview

The workspace uses a dusk-lit ledger with meadow greens and warm highlights. This is a product interface for recording savings, debt repayments and bill reminders. English is the current UI language; existing currency formatting remains owned by `frontend/src/api.ts`. The app records financial activity and does not process payments or move money.

The signature is a restrained paycheque action at the top-right of the Budget header. Goals and debts have the strongest action hierarchy; their circular add controls follow the existing items instead of competing with section headings. Bills are supporting reminders. The landing page keeps its separate marketing composition.

## Colors

Warm Gouache follows the requested approximate 60/30/10 balance: Warm Totoro Cream #FAF8F5 for the dominant canvas, Laputa Sky #4F6D7A for navigation, text and structural emphasis, and Meadow Green #A8BE91 for primary actions and highlights. Cards are cream-toned #F4F3EF with soft blue-grey borders #A7B6BA. Statement spotlight and navigation use dusty-blue surfaces with cream text. Warm supporting panels use #E9EEDF.

Body text #344E5A and supporting text #4F6D7A are legible on cream. Green controls use dark #293E48 labels; blue secondary and terracotta danger controls use cream labels. Danger #A04F36 retains its textual meaning. Native controls use light colour-scheme. Focus is dusty blue; semantic status washes remain subtle. Colour roles are shared across pages; Noto Sans and layouts remain.

Runtime ownership: frontend/src/index.css owns the palette and shadow tokens. styles/colors.css assigns structural and semantic surfaces. Shared cards use a soft blue-grey shadow (0 4px 18px at 9%); the statement spotlight uses 0 10px 30px at 13%. Budget and route CSS consume these tokens. No decorative background imagery is added.

## Typography

Noto Sans carries headings, controls, body text and financial values across the site. `frontend/index.html` loads regular, medium, semibold, bold and italic faces through Google Fonts with display=swap. `frontend/src/index.css` owns the shared `--font-site` token, with system sans as the fallback. Headings use semibold. Amounts use tabular numerals. Headings scale from 2.4 to 3.25rem; list headings are 1.65rem. Supporting copy remains readable at .85rem. Long names and descriptions wrap rather than truncate.

## Layout

The desktop sidebar uses a compact 190px width, 18px header spacing and 4px navigation gaps. A vertically centred edge control collapses it to a 24px rail, keeping the control visible so the navigation can always be reopened. Links retain 44px minimum height and readable text; mobile keeps the existing two-column navigation with tighter outer padding and does not collapse.

Dashboard is a compact financial overview using the same sky, meadow and warm accent theme. Four separate totals show account balances, total goal savings, remaining debt and all recorded bill amounts. Bounded previews keep accounts and progress prominent; bills and the latest statement support them. `styles/overview.css` consumes the budget tokens and scopes layout to `.overview-page`. It uses the shared StatCard and business-specific DashboardPanel, with links instead of editing forms. Container breakpoints adapt the open lists and progress sections to the available width. Budget now opens directly with the paycheque planning strip and management lists. Empty URLs enter Dashboard while the explicit landing route remains available through the brand.

Every page fills the available screen width, with responsive outer padding and no centred page max-width. Hero copy retains a readable line length. The existing full-width sidebar shell remains. Content container breakpoints at 1100, 820 and 580px account for the actual available width. Above 1100px, two primary columns sit beside a 290px bills panel. Below that, bills follow goals and debts; below 580px the primary columns and summary ledger stack. The page owns natural document scrolling. No page height or overflow lock is added. Modal content scrolls within its established viewport limit.

## Elevation & Depth

Use thin borders and tonal surfaces for hierarchy. Reserve shadow and backdrop for dialogs. Avoid decoration or new imagery that competes with progress and actions.

## Shapes

Panels use 12px corners, controls 7px, and goal/debt rows 8px. Progress tracks are slim rounded bars. Empty states use a quiet circular plus marker paired with real action text.

## Components

`StatCard` remains the reusable summary owner. `CollapsibleItem` retains native details interaction. `EmptyState` provides title, explanation and a working creation action. Forms use `AppForm` for owned constraint feedback, linked errors, first invalid focus, and duplicate submission protection. `AutoTextarea` grows with input. Date fields and the Accounts select deliberately retain browser/OS popup ownership.

`Modal` owns native dialog focus trapping, Escape, trigger focus restoration, busy close prevention and an app-owned discard prompt after edits. `Notice` and `useNotice` retain the existing inline overlay and three-second lifetime. `DeleteItem` remains the named-object confirmation owner.

Buttons have deliberate hover, pressed, focus and disabled states. Budget targets are at least 44px high. Loading keeps the summary footprint stable. Errors remain inline and retain entered data. Primary actions are labelled with verbs; destructive confirmation uses its existing danger treatment. No new icon dependency is needed; the disclosure chevron and decorative plus retain text equivalents.

Motion uses a 140ms colour transition, a 1px pressed response, and a 280ms eased expansion/collapse on Budget goal, debt and bill cards. Native details animates intrinsic height where supported and falls back to immediate disclosure elsewhere; bills use a grid-row transition with collapsed content inert and hidden from accessibility. Reduced motion disables transitions. Scrollbars inherit global thumb, track, hover and active tokens with standards and WebKit support.

Your Budget Wrapped uses `StatementLibrary` for a quiet list of file names, date
ranges, and transaction counts. Each row navigates to a file-specific summary.
`StatementDetail` reuses StatCard and the existing scrolling transaction table.
`styles/statements.css` consumes the established budget tokens; it introduces no
new palette or typography. File names wrap, and document scrolling remains natural.

## Do's and Don'ts

- Do keep goals and debts prominent and bills supporting.
- Do reuse shared validation, feedback and modal owners.
- Do distinguish recorded money from actual money movement.
- Don't change business rules through visual styling.
- Don't use hover as the only route to details.
- Don't give every region equally strong borders, headings and action emphasis.

Paycheque allocation now includes accounts using the existing grouped numeric fields and record dialog. Account deposits update recorded balances only when completed; linked goal deposits update the account and earmarked goal together; each dollar is allocated once. Paycheque deletion uses DeleteItem confirmation, removing its plans/history while preserving completed savings, balances and payments. Policy source: backend/app/services/paycheques.py.

Account-backed goals: GoalAccountSelect reuses native select, AppForm and existing feedback. Optional links preserve older goals. Linked current_amount earmarks existing account money; direct goal additions assign existing funds and cannot exceed the account balance. Paycheque completion records a new deposit in both linked goal and account atomically. Account balance edits cannot reduce the balance below earmarked funds. Unlinking/deleting a goal releases its earmark without changing account balance. Source: backend/app/services/goals.py and backend/app/services/paycheques.py.

Goal card summaries show the linked account, or No linked account, without expansion. Paid-off debts reuse DeleteItem with a Resolve debt variant and explicit confirmation that recorded payments remain in Activity history. The backend rechecks zero remaining balance before resolution. Source: backend/app/routers/debts.py.

CollapsibleItem supports an optional cardAction outside the details disclosure. Paid-off debts show Resolve debt there even while collapsed, with the same DeleteItem confirmation and backend balance guard.

Dashboard unboxed totals reuse StatCard and the existing abortable resources. Total saved sums goal current amounts without adding account balances; Total debt sums remaining balances; Total bills sums all recorded bill amounts including paid bills and is explicitly not a monthly projection. Summary totals use four columns on wide screens and two on narrower screens.

Accounts uses one full-width neutral stack with divided rows, shared typography, and inline balance actions. Each row shows account identity, earmarked and unassigned money, and the manually recorded balance. The balance button opens AppForm with a selected numeric input, Enter/Save commits, Cancel/Escape uses the shared discard guard, and success returns focus to the balance. Server errors retain the input; linked goal limits remain server-owned. Name/type edits and creation retain AccountForm/Modal. Linked goals are available through native details. Rows reflow at available container widths of 850px and 540px; document scrolling remains natural. Runtime layout owner: frontend/src/styles/accounts.css.


Paycheque planner lives at #/budget/paycheques as an indented Budget navigation child. PaychequePlan owns the guided page worksheet using AppForm, native date inputs and existing account/goal/debt targets; PaychequeAllocations, PaychequeHistory and DeleteItem retain recording, history and deletion behavior. Received money, bills/everyday reserves and allocations are saved atomically. Reserves reduce remaining money but never update bills or balances. Desktop uses a sticky review panel; narrow screens show a sticky remaining amount above the worksheet. Save stays on the page with the actual saved plan. No automatic financial recommendations are made. Reserves are fixed for a saved paycheque; cancelled pending allocations release only their allocation amounts.

StatementDetail first offers an optional six-screen Budget Wrapped using StatementWrapped; skip, exit, finish and replay retain the statement summary and table. Each screen is manually advanced with Back/Next or six accessible progress buttons, with heading focus on change, shared currency/date formatting, reduced-motion support and scoped accent tokens. Insights load from the selected statement /insights endpoint with abort, retry and exit recovery. Money in/out include transfers; exact descriptions are not merchant or item classifications; largest movement includes either debit or credit; highest spending excludes nonpositive debit days and ties use earliest date.

Wrapped insight details: the largest transaction returns amount, debit/credit kind, description and date, with deterministic ties. The highest-spending day returns its positive-debit total and all same-statement transactions on that date. The final slide shows a separate debit/credit table, ten rows per page, including credits without deducting them from spending. Existing table/scroll styles, currency formatting and controls are reused.

Dashboard uses an open ledger layout: four unboxed totals, divided account/bill lists, borderless goal/debt progress sections, and one neutral latest-statement surface. Copy is concise; goal/account overlap and recorded-bill scope remain explicit. The main action opens the paycheque planner. Existing resources, bounded previews, retries and financial calculations are unchanged. overview.css owns dashboard layout and container breakpoints (1000/640/420px), reusing index.css tokens and Noto Sans.

Dashboard hierarchy: goal/debt progress leads the main column with larger headings and thicker progress tracks. Latest statement sits at upper right with a sky-filled “View Your Budget Wrapped” link to that statement. Accounts and a compact three-bill preview follow below. Below 680px the reading order is progress, statement, accounts, bills; progress columns stack below 440px. Existing totals and retries remain.


Activity history lives at #/activity and follows the open ledger language: a quiet
header, linked kind filters, and a semantic table whose saved target name leads
each row. Small labelled sage/rose/gold markers distinguish goal/debt/bill records;
financial amounts use tabular numerals. All colours come from index.css tokens.
styles/activity.css owns this page's layout without changing the app shell.
Native link navigation preserves kind/page in the URL; 20-record server pagination,
shared abortable resource loading/retry, separate empty states and a named horizontal
scroll region keep the ledger usable on narrow screens. Payment dates are date-only;
recording timestamps include the viewer's timezone. Deleted targets retain readable
names. DeleteItem confirmations explain history retention. The canonical behavior
map is maintained in UX-CONTRACT.md.

Dashboard simplification: three recorded totals (accounts, saved toward goals, remaining debt), one conditional next-payment/overdue reminder, and three-item goal/debt previews. Unfinished goals lead via a stable copied sort; completed goals remain in the full view. Statement and compact bills share a right rail; accounts are a supporting two-column list. Mobile stacks naturally with account total leading. Recorded bills aggregate is removed from this overview to avoid competing with date-specific reminders; Budget remains its owner. Existing resources, error/retry and money semantics are preserved.

Budget Wrapped now opens saved files directly into their summary instead of an invitation gate. Play Budget Wrapped retains the existing optional six-screen experience and summary return/focus. The library is an open list with latest-upload label and a supporting upload panel; CSV format guidance is disclosed on request. Summary shows money in, money out and net movement (credits minus debits using sumAmounts), explicitly file-scoped and not savings. Review transactions focuses and scrolls to the table heading without changing the route. Existing uploads, 20-file/50-row paging, original-file downloads, abort/retry, and backend insights remain. statements.css owns layout at container widths 760/480px using shared tokens.

The primary accent is soft meadow green #A8BE91, with hover #9AB381 and dark labels #293E48. Supporting accent surfaces use pale meadow #E9EEDF. This replaces sunset amber while retaining cream and dusty-blue foundations. Runtime owner: index.css.


Activity payment rows include a quiet outlined Undo action with a decorative curved
back arrow and a visible label. UndoPayment reuses Modal for named-amount confirmation,
busy close prevention, focus restoration and inline errors, and Notice/useNotice for
confirmed success. Existing surface, border, danger and focus tokens own all states;
no palette changes. Disabled undo actions show their explanation in the row. The
semantic Actions column remains reachable through the existing horizontal scroll
region on narrow screens. Successful undo refetches server totals, clamps paging
and focuses the ledger heading. No optimistic financial changes are shown.
