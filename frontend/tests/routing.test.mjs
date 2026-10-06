import test from 'node:test'
import assert from 'node:assert/strict'
import { parseHash, statementIdFromHash } from '../src/routing.ts'

test('statement links retain the Wrapped page route and parse their ID separately', () => {
  for (const hash of ['#/budget-wrapped?statement=1', '#/budget-wrapped/?statement=1']) {
    assert.equal(parseHash(hash).path, '#/budget-wrapped')
    assert.equal(statementIdFromHash(hash), 1)
  }
  assert.equal(statementIdFromHash('#/budget-wrapped?statement=2'), 2)
  assert.equal(statementIdFromHash('#/budget-wrapped'), null)
})

test('base routes, empty URLs and unknown routes remain distinct', () => {
  assert.equal(parseHash('').path, '#/dashboard')
  assert.equal(parseHash('#/dashboard').path, '#/dashboard')
  assert.equal(parseHash('#/').path, '#/')
  assert.equal(parseHash('#/budget?anything=1').path, '#/budget')
  assert.equal(parseHash('#/accounts').path, '#/accounts')
  assert.equal(parseHash('#/unknown?statement=1').path, '#/unknown')
})

test('invalid statement IDs do not select a detail view', () => {
  for (const value of ['0', '-1', 'abc', '1.5', '9007199254740992']) {
    assert.equal(statementIdFromHash(`#/budget-wrapped?statement=${value}`), null)
  }
})
