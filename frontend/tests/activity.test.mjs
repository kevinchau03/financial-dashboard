import test from 'node:test'
import assert from 'node:assert/strict'
import { activityFilters, activityHref, paymentDate } from '../src/activity.ts'

test('activity links restore filters and pagination and discard invalid query state', () => {
  assert.deepEqual(activityFilters('#/activity?kind=goal&page=3'), { kind: 'goal', page: 3 })
  for (const page of ['0', '-2', '1.5', 'NaN', '1000001', '2e3']) {
    assert.deepEqual(activityFilters(`#/activity?kind=invalid&page=${page}`), { kind: 'all', page: 1 })
  }
  assert.equal(activityHref('goal'), '#/activity?kind=goal')
  assert.equal(activityHref('all'), '#/activity')
  assert.equal(activityHref('debt', 2), '#/activity?kind=debt&page=2')
})

test('calendar payment dates preserve their day in local time', () => {
  assert.equal(paymentDate('2026-01-01'), new Date(2026, 0, 1, 12).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }))
})
