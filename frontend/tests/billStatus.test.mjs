import { test } from 'node:test'
import assert from 'node:assert/strict'
import { billStatus } from '../src/billStatus.ts'

const bill = { recurring: true, is_paid: false, due_date: '2026-11-05', payments: [{ due_date: '2026-10-05' }] }
test('paid until the next due date, unpaid on it, overdue after it', () => {
  assert.equal(billStatus(bill, '2026-10-05'), 'paid')
  assert.equal(billStatus(bill, '2026-11-04'), 'paid')
  assert.equal(billStatus(bill, '2026-11-05'), 'unpaid')
  assert.equal(billStatus(bill, '2026-11-06'), 'overdue')
})
test('new recurring bills remain unpaid until a payment is recorded', () => {
  assert.equal(billStatus({ ...bill, payments: [] }, '2026-10-05'), 'unpaid')
  assert.equal(billStatus({ ...bill, payments: [] }, '2026-11-06'), 'overdue')
})
test('late payments do not hide still-overdue occurrences', () => {
  assert.equal(billStatus({ ...bill, due_date: '2026-10-01', payments: [{ due_date: '2026-09-01' }] }, '2026-10-05'), 'overdue')
})
test('one-time paid bills stay paid and unscheduled bills are supported', () => {
  assert.equal(billStatus({ ...bill, recurring: false, is_paid: true }, '2027-01-01'), 'paid')
  assert.equal(billStatus({ ...bill, due_date: null, payments: [] }, '2026-10-05'), 'unpaid')
})
