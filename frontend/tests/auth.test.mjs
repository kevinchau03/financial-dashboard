import test from 'node:test'
import assert from 'node:assert/strict'
import { apiFetch, getAuthClient, sessionExpiredEvent } from '../src/auth.ts'

test('authenticated requests protect tokens, preserve request options, and distinguish outages from expired sessions', async t => {
  const originalFetch = globalThis.fetch
  const originalWindow = globalThis.window
  const storage = new Map()
  const browser = new EventTarget()
  browser.sessionStorage = {
    getItem: key => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: key => storage.delete(key),
  }
  globalThis.window = browser
  let expired = 0
  browser.addEventListener(sessionExpiredEvent, () => expired++)
  const sub = '00000000-0000-4000-8000-000000000001'
  const encode = data => Buffer.from(JSON.stringify(data)).toString('base64url')
  const now = Math.floor(Date.now() / 1000)
  const token = `${encode({ alg: 'HS256' })}.${encode({ sub, aud: 'authenticated', exp: now + 3600, iat: now })}.fixture`
  let responseStatus = 200
  let lastRequest
  let financialRequests = 0
  globalThis.fetch = async (input, init) => {
    const url = String(input)
    if (url === '/api/auth/config') return Response.json({ url: 'https://auth-test.supabase.co', publishable_key: 'sb_publishable_fixture' })
    if (url.startsWith('https://auth-test.supabase.co/auth/v1/token')) return Response.json({
      access_token: token, refresh_token: 'test-refresh', expires_in: 3600,
      token_type: 'bearer', user: { id: sub, email: 'owner@example.test', role: 'authenticated', aud: 'authenticated' },
    })
    if (url.startsWith('https://auth-test.supabase.co/auth/v1/logout')) return new Response(null, { status: 204 })
    assert.equal(url, '/api/accounts')
    financialRequests++
    lastRequest = init
    return Response.json({}, { status: responseStatus })
  }
  let client
  t.after(() => {
    client?.auth.stopAutoRefresh()
    globalThis.fetch = originalFetch
    globalThis.window = originalWindow
  })
  await assert.rejects(apiFetch('https://untrusted.example/api/accounts'), /application API URL/)
  client = await getAuthClient()
  const login = await client.auth.signInWithPassword({ email: 'owner@example.test', password: 'password12' })
  assert.equal(login.error, null)
  const controller = new AbortController()
  await apiFetch('/api/accounts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', signal: controller.signal })
  assert.equal(lastRequest.headers.get('Authorization'), `Bearer ${token}`)
  assert.equal(lastRequest.headers.get('Content-Type'), 'application/json')
  assert.equal(lastRequest.signal, controller.signal)
  assert.equal(lastRequest.method, 'POST')
  assert.equal(lastRequest.cache, 'no-store')
  responseStatus = 503
  assert.equal((await apiFetch('/api/accounts')).status, 503)
  assert.equal(expired, 0)
  responseStatus = 401
  await assert.rejects(apiFetch('/api/accounts'), /session has ended/)
  assert.equal(expired, 1)
  await client.auth.signOut({ scope: 'local' })
  const previousRequests = financialRequests
  await assert.rejects(apiFetch('/api/accounts'), /session has ended/)
  assert.equal(financialRequests, previousRequests)
})
