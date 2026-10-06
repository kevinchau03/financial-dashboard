import test from 'node:test'
import assert from 'node:assert/strict'
import { sumAmounts, upcomingBills } from '../src/dashboardSummary.ts'

test('summaries add cents without merging accounts and goal balances', () => {
  assert.equal(sumAmounts(['0.10', '0.20']), '0.3')
  assert.equal(sumAmounts([]), '0')
  assert.equal(sumAmounts(['100', '-25.25']), '74.75')
})

test('bill reminders retain recurring next payments and exclude settled one-time bills', () => {
  const bills = [
    { id: 1, recurring: false, is_paid: true, due_date: '2026-01-01' },
    { id: 2, recurring: true, is_paid: true, due_date: '2026-11-01' },
    { id: 3, recurring: false, is_paid: false, due_date: null },
    { id: 4, recurring: false, is_paid: false, due_date: '2026-10-01' },
  ]
  assert.deepEqual(upcomingBills(bills).map(bill => bill.id), [4, 2, 3])
  assert.equal(bills.length, 4)
})
