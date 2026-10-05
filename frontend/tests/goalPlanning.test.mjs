import { test } from 'node:test'
import assert from 'node:assert/strict'
import { savingsPlan } from '../src/goalPlanning.ts'

test('monthly pace rounds up to cents and includes a contribution today', () => {
  const plan = savingsPlan('100', '0', '2027-01-03', '2026-10-04')
  assert.equal(plan.months, 3)
  assert.equal(plan.monthly, 3334)
})
test('month end, leap year, and year boundary', () => {
  assert.equal(savingsPlan('100', '0', '2024-02-29', '2024-01-31').months, 2)
  assert.equal(savingsPlan('100', '0', '2025-02-28', '2025-01-31').months, 2)
  assert.equal(savingsPlan('100', '0', '2026-01-15', '2025-12-15').months, 2)
})
test('today, no date, overdue, and funded goals', () => {
  assert.equal(savingsPlan('100', '25', '2026-10-04', '2026-10-04').monthly, 7500)
  assert.equal(savingsPlan('100', '25', null, '2026-10-04').status, 'flexible')
  assert.equal(savingsPlan('100', '25', '2026-10-03', '2026-10-04').status, 'past-due')
  assert.equal(savingsPlan('100', '101', '2026-10-03', '2026-10-04').status, 'funded')
  assert.equal(savingsPlan('0.30', '0.10', null, '2026-10-04').remaining, 20)
})
