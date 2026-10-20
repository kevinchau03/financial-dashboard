---
version: alpha
name: MyBudgetPro
description: A calm personal budget workspace with neutral dark surfaces and earthy action accents.
colors:
  primary: "#a5b99a"
  background: "#181a1b"
  surface: "#232628"
  text: "#eeece7"
  muted: "#b5b3ad"
  wash: "#232628"
  border: "#484c4e"
  focus: "#9ebac8"
  danger: "#cd967e"
  leaf-accent: "#a5b99a"
  leaf-surface: "#232628"
  sky-accent: "#9ebac8"
  sky-surface: "#232628"
  sun-accent: "#d5b66c"
  sun-surface: "#232628"
  rose-accent: "#c59caa"
  rose-surface: "#232628"
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
  button: { backgroundColor: "{colors.primary}", textColor: "{colors.background}" }
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

## Overview

The workspace uses a quiet charcoal ledger with earthy highlights. This is a product interface for recording savings, debt repayments and bill reminders. English is the current UI language; existing currency formatting remains owned by `frontend/src/api.ts`. The app records financial activity and does not process payments or move money.

The signature is a restrained paycheque action at the top-right of the Budget header. Goals and debts have the strongest action hierarchy; their circular add controls follow the existing items instead of competing with section headings. Bills are supporting reminders. The landing page keeps its separate marketing composition.

## Colors

Dark mode uses neutral charcoal throughout: background #181a1b, cards #232628, hover surfaces #303436, text #eeece7, supporting text #b5b3ad, and borders #484c4e. All cards and ordinary headings/values share these colours across routes. Only buttons and highlighted elements (progress, status badges, focus rings, and thin accent edges) use earthy colours: sage #a5b99a, warm sky #9ebac8, gold #d5b66c, dusty rose #c59caa, and terracotta #cd967e. Accent-filled buttons use #181a1b labels for contrast. Danger retains explicit textual context.

Runtime ownership: `frontend/src/index.css` owns the palette and font tokens. `App.css` and route styles consume those tokens; `styles/budget.css` adapts them to existing `--budget-*` aliases and neutral scrollbar tokens. `styles/colors.css` owns shared semantic accent treatments. DESIGN.md documents runtime values; it does not generate CSS.

## Typography

Noto Sans carries headings, controls, body text and financial values across the site. `frontend/index.html` loads regular, medium, semibold, bold and italic faces through Google Fonts with display=swap. `frontend/src/index.css` owns the shared `--font-site` token, with system sans as the fallback. Headings use semibold. Amounts use tabular numerals. Headings scale from 2.4 to 3.25rem; list headings are 1.65rem. Supporting copy remains readable at .85rem. Long names and descriptions wrap rather than truncate.

## Layout

The desktop sidebar uses a compact 190px width, 18px header spacing and 4px navigation gaps. A vertically centred edge control collapses it to a 24px rail, keeping the control visible so the navigation can always be reopened. Links retain 44px minimum height and readable text; mobile keeps the existing two-column navigation with tighter outer padding and does not collapse.

Dashboard is a compact financial overview using the same dark neutral theme and earthy accents. Four separate totals show account balances, total goal savings, remaining debt and all recorded bill amounts. Bounded previews keep accounts and progress prominent; bills and the latest statement support them. `styles/overview.css` consumes the budget tokens and scopes layout to `.overview-page`. It uses the shared StatCard and business-specific DashboardPanel, with links instead of editing forms. Below 1200px the secondary panels follow the primary area, and narrow layouts stack naturally. Budget now opens directly with the paycheque planning strip and management lists. Empty URLs enter Dashboard while the explicit landing route remains available through the brand.

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

Goal card summaries show the linked account, or No linked account, without expansion. Paid-off debts reuse DeleteItem with a Resolve debt variant and explicit payment-history deletion confirmation. The backend rechecks zero remaining balance before resolution. Source: backend/app/routers/debts.py.

CollapsibleItem supports an optional cardAction outside the details disclosure. Paid-off debts show Resolve debt there even while collapsed, with the same DeleteItem confirmation and backend balance guard.

Dashboard summary cards reuse StatCard and the existing abortable resources. Total saved sums goal current amounts without adding account balances; Total debt sums remaining balances; Total bills sums all recorded bill amounts including paid bills and is explicitly not a monthly projection. Summary cards use four columns on wide screens, two on intermediate widths and one on mobile.

Accounts uses one full-width neutral stack with divided rows, shared typography, and inline balance actions. Each row shows account identity, earmarked and unassigned money, and the manually recorded balance. The balance button opens AppForm with a selected numeric input, Enter/Save commits, Cancel/Escape uses the shared discard guard, and success returns focus to the balance. Server errors retain the input; linked goal limits remain server-owned. Name/type edits and creation retain AccountForm/Modal. Linked goals are available through native details. Rows reflow at available container widths of 850px and 540px; document scrolling remains natural. Runtime layout owner: frontend/src/styles/accounts.css.


Paycheque planner lives at #/budget/paycheques as an indented Budget navigation child. PaychequePlan owns the guided page worksheet using AppForm, native date inputs and existing account/goal/debt targets; PaychequeAllocations, PaychequeHistory and DeleteItem retain recording, history and deletion behavior. Received money, bills/everyday reserves and allocations are saved atomically. Reserves reduce remaining money but never update bills or balances. Desktop uses a sticky review panel; narrow screens show a sticky remaining amount above the worksheet. Save stays on the page with the actual saved plan. No automatic financial recommendations are made. Reserves are fixed for a saved paycheque; cancelled pending allocations release only their allocation amounts.

StatementDetail first offers an optional six-screen Budget Wrapped using StatementWrapped; skip, exit, finish and replay retain the statement summary and table. Each screen is manually advanced with Back/Next or six accessible progress buttons, with heading focus on change, shared currency/date formatting, reduced-motion support and scoped accent tokens. Insights load from the selected statement /insights endpoint with abort, retry and exit recovery. Money in/out include transfers; exact descriptions are not merchant or item classifications; largest movement includes either debit or credit; highest spending excludes nonpositive debit days and ties use earliest date.

Wrapped insight details: the largest transaction returns amount, debit/credit kind, description and date, with deterministic ties. The highest-spending day returns its positive-debit total and all same-statement transactions on that date. The final slide shows a separate debit/credit table, ten rows per page, including credits without deducting them from spending. Existing table/scroll styles, currency formatting and controls are reused.
