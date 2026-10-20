import test from 'node:test'
import assert from 'node:assert/strict'
import { transactionOccurrences } from '../src/statementInsights.ts'

const rows = [['2026-01-01', 'Cafe', '10', null], ['2026-01-02', 'Cafe', null, '5'], ['2026-01-02', 'Cafe #2', '2', null]]
test('legacy API counts exact descriptions across debits and credits without crashing', () => {
  assert.equal(transactionOccurrences('Cafe', undefined, rows), 2)
  assert.equal(transactionOccurrences('Cafe #2', undefined, rows), 1)
  assert.equal(transactionOccurrences(null, undefined, rows), 0)
})
test('valid API counts are used; invalid counts fall back to statement rows', () => {
  assert.equal(transactionOccurrences('Cafe', 2, rows), 2)
  for (const count of [null, NaN, -1, 0, 1.5]) assert.equal(transactionOccurrences('Cafe', count, rows), 2)
})
