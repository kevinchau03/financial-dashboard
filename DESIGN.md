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
typography:
  sans:
    fontFamily: "system-ui, sans-serif"
  display:
    fontFamily: "Georgia, serif"
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
---

# MyBudgetPro Design System

## Overview

The Budget workspace carries the existing Howl's Moving Castle inspired cream and green identity through a quiet paper-and-ledger composition. This is a product interface for recording savings, debt repayments and bill reminders. English is the current UI language; existing currency formatting remains owned by `frontend/src/api.ts`. No new market, payment processing or account allocation rules are introduced.

The signature is a soft green paycheque strip beneath a restrained summary ledger. Goals and debts have the strongest action hierarchy; bills are supporting reminders. The landing page keeps its separate marketing composition.

## Colors

Runtime ownership: `frontend/src/styles/budget.css` defines the `--budget-*` and `--scroll-*` tokens. This document mirrors those values; it does not generate CSS. `Budget.tsx` imports that stylesheet, with page selectors scoped to `.budget-page`. Existing shared styles in `App.css` and `index.css` remain the baseline for sibling routes. The Budget background, focus and danger colours inherit that baseline. Future changes must update both this map and the matching runtime variables or inherited rule.

Paper is `surface`; moss is primary action emphasis; wash separates guidance and the paycheque strip. Danger is textual as well as coloured. Forced colours retain native control and scrollbar semantics.

## Typography

Georgia carries page and column headings. System sans carries controls, body text and financial values. Amounts use tabular numerals. Headings scale from 2.4 to 3.25rem; list headings are 1.65rem. Supporting copy remains readable at .85rem. Long names and descriptions wrap rather than truncate.

## Layout

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

## Do's and Don'ts

- Do keep goals and debts prominent and bills supporting.
- Do reuse shared validation, feedback and modal owners.
- Do distinguish recorded money from actual money movement.
- Don't change business rules through visual styling.
- Don't use hover as the only route to details.
- Don't give every region equally strong borders, headings and action emphasis.
