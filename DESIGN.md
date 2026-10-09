---
version: alpha
name: MyBudgetPro
description: A calm personal budget workspace in cream, moss green and soft sky tones.
colors:
  primary: "#3f5e48"
  background: "#f3efdf"
  surface: "#fffdf6"
  text: "#303f38"
  muted: "#5c665c"
  wash: "#e4ece9"
  border: "#d5d9c9"
  focus: "#6e9bb2"
  danger: "#a13e2b"
  leaf-accent: "#2f6447"
  leaf-surface: "#eaf3e4"
  sky-accent: "#285f7b"
  sky-surface: "#e7f1f7"
  sun-accent: "#805b18"
  sun-surface: "#fff2cf"
  rose-accent: "#954a3b"
  rose-surface: "#faeae2"
typography:
  sans:
    fontFamily: "Open Sans, system-ui, sans-serif"
  display:
    fontFamily: "Open Sans, system-ui, sans-serif"
rounded:
  DEFAULT: "12px"
  control: "7px"
spacing:
  section-gap: "28px"
  card-padding: "16px"
components:
  button: { backgroundColor: "{colors.primary}", textColor: "{colors.surface}" }
  card: { backgroundColor: "{colors.surface}", textColor: "{colors.text}" }
  dialog: { backgroundColor: "{colors.surface}", textColor: "{colors.text}" }
  guidance: { backgroundColor: "{colors.wash}", textColor: "{colors.muted}" }
  divider: { backgroundColor: "{colors.border}" }
  focus-ring: { backgroundColor: "{colors.focus}" }
  error-text: { textColor: "{colors.danger}" }
  savings-card: { backgroundColor: "{colors.leaf-surface}", textColor: "{colors.leaf-accent}" }
  accounts-card: { backgroundColor: "{colors.sky-surface}", textColor: "{colors.sky-accent}" }
  bills-card: { backgroundColor: "{colors.sun-surface}", textColor: "{colors.sun-accent}" }
  debt-card: { backgroundColor: "{colors.rose-surface}", textColor: "{colors.rose-accent}" }
---

Paycheque planning extends the Budget page's cream and moss palette. Keep entry compact, use a modal for the allocation worksheet, show three calm numeric totals and group targets into goals, debts and accounts. Use explicit Planned and Recorded labels instead of showing projected progress as actual savings. History stays behind a button and allocation details are collapsible. Reuse the shared form, dialog, notice, focus and scrollbar patterns; retain native date selection. Narrow screens keep amount fields readable without horizontal overflow.

# MyBudgetPro Design System

## Overview

The Budget workspace carries the existing Howl's Moving Castle inspired cream and green identity through a quiet paper-and-ledger composition. This is a product interface for recording savings, debt repayments and bill reminders. English is the current UI language; existing currency formatting remains owned by `frontend/src/api.ts`. The app records financial activity and does not process payments or move money.

The signature is a soft sky paycheque strip above the management lists. Goals and debts have the strongest action hierarchy; bills are supporting reminders. The landing page keeps its separate marketing composition.

## Colors

`frontend/src/index.css` owns four shared accent/surface pairs: sky for accounts and statement context, leaf for savings and income, rose for debt and outflow, and sun for bills. `styles/colors.css` applies optional semantic `data-tone` variants on StatCard and DashboardPanel, plus the corresponding Budget, Accounts and landing surfaces. Dark coloured headings and values sit on pale backgrounds; ordinary text and error states retain their existing colours. Thin accent edges and gentle panel washes add emphasis without introducing motion or changing layout. Labels remain the primary meaning, so colour is never the only cue.

Runtime ownership: `frontend/src/styles/budget.css` defines the `--budget-*` and `--scroll-*` tokens. This document mirrors those values; it does not generate CSS. `Budget.tsx` imports that stylesheet, with page selectors scoped to `.budget-page`. Existing shared styles in `App.css` and `index.css` remain the baseline for sibling routes. The Budget background, focus and danger colours inherit that baseline. Future changes must update both this map and the matching runtime variables or inherited rule.

Paper is `surface`; moss is primary action emphasis; wash separates guidance and the paycheque strip. Danger is textual as well as coloured. Forced colours retain native control and scrollbar semantics.

## Typography

Open Sans carries headings, controls, body text and financial values across the site. `frontend/index.html` loads regular, medium, semibold, bold and italic faces through Google Fonts with display=swap. `frontend/src/index.css` owns the shared `--font-site` token, with system sans as the fallback. Headings use semibold. Amounts use tabular numerals. Headings scale from 2.4 to 3.25rem; list headings are 1.65rem. Supporting copy remains readable at .85rem. Long names and descriptions wrap rather than truncate.

## Layout

The desktop sidebar uses a compact 190px width, 18px header spacing and 4px navigation gaps. Links retain 44px minimum height and readable text; mobile keeps the existing two-column navigation with tighter outer padding.

Dashboard is a compact financial overview using the same cream, moss and sky theme. Four separate totals show account balances, total goal savings, remaining debt and all recorded bill amounts. Bounded previews keep accounts and progress prominent; bills and the latest statement support them. `styles/overview.css` consumes the budget tokens and scopes layout to `.overview-page`. It uses the shared StatCard and business-specific DashboardPanel, with links instead of editing forms. Below 1200px the secondary panels follow the primary area, and narrow layouts stack naturally. Budget now opens directly with the paycheque planning strip and management lists. Empty URLs enter Dashboard while the explicit landing route remains available through the brand.

The existing full-width sidebar shell remains. Content container breakpoints at 1100, 820 and 580px account for the actual available width. Above 1100px, two primary columns sit beside a 290px bills panel. Below that, bills follow goals and debts; below 580px the primary columns and summary ledger stack. The page owns natural document scrolling. No page height or overflow lock is added. Modal content scrolls within its established viewport limit.

## Elevation & Depth

Use thin borders and tonal surfaces for hierarchy. Reserve shadow and backdrop for dialogs. Avoid decoration or new imagery that competes with progress and actions.

## Shapes

Panels use 12px corners, controls 7px, and goal/debt rows 8px. Progress tracks are slim rounded bars. Empty states use a quiet circular plus marker paired with real action text.

## Components

`StatCard` remains the reusable summary owner. `CollapsibleItem` retains native details interaction. `EmptyState` provides title, explanation and a working creation action. Forms use `AppForm` for owned constraint feedback, linked errors, first invalid focus, and duplicate submission protection. `AutoTextarea` grows with input. Date fields and the Accounts select deliberately retain browser/OS popup ownership.

`Modal` owns native dialog focus trapping, Escape, trigger focus restoration, busy close prevention and an app-owned discard prompt after edits. `Notice` and `useNotice` retain the existing inline overlay and three-second lifetime. `DeleteItem` remains the named-object confirmation owner.

Buttons have deliberate hover, pressed, focus and disabled states. Budget targets are at least 44px high. Loading keeps the summary footprint stable. Errors remain inline and retain entered data. Primary actions are labelled with verbs; destructive confirmation uses its existing danger treatment. No new icon dependency is needed; the disclosure chevron and decorative plus retain text equivalents.

Motion is limited to a 140ms colour transition and a 1px pressed response. Reduced motion disables transitions. Scrollbars inherit global thumb, track, hover and active tokens with standards and WebKit support.

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
