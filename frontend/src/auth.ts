import type { SupabaseClient } from '@supabase/supabase-js'

let clientPromise: Promise<SupabaseClient> | undefined
export const sessionExpiredEvent = 'budget-session-expired'

export function getAuthClient() {
  clientPromise ??= (async () => {
    const [response, { createClient }] = await Promise.all([
      fetch('/api/auth/config', { signal: AbortSignal.timeout(10000), cache: 'no-store' }),
      import('@supabase/supabase-js'),
    ])
    if (!response.ok) throw new Error('Sign-in is not available. Check the server’s Supabase settings, then try again.')
    const config: { url: string; publishable_key: string } = await response.json()
    return createClient(config.url, config.publishable_key, {
      auth: { persistSession: true, storage: window.sessionStorage, autoRefreshToken: true, detectSessionInUrl: false },
      global: { fetch: (input, init) => fetch(input, { ...init, signal: init?.signal
        ? AbortSignal.any([init.signal, AbortSignal.timeout(15000)]) : AbortSignal.timeout(15000) }) },
    })
  })().catch(error => { clientPromise = undefined; throw error })
  return clientPromise
}

/** Attach a current session only to this app's API, including protected files. */
export async function apiFetch(url: string, init: RequestInit = {}) {
  if (!url.startsWith('/api/')) throw new Error('Expected an application API URL.')
  const client = await getAuthClient()
  const { data, error } = await client.auth.getSession()
  if (error || !data.session) {
    window.dispatchEvent(new Event(sessionExpiredEvent))
    throw new Error('Your session has ended. Sign in to continue.')
  }
  const headers = new Headers(init.headers)
  headers.set('Authorization', `Bearer ${data.session.access_token}`)
  const response = await fetch(url, { ...init, headers, cache: 'no-store' })
  if (response.status === 401) {
    // An old request must not expire a newly signed-in or refreshed session.
    const latest = await client.auth.getSession()
    if (latest.data.session?.access_token === data.session.access_token) window.dispatchEvent(new Event(sessionExpiredEvent))
    throw new Error('Your session has ended. Sign in to continue.')
  }
  return response
}
