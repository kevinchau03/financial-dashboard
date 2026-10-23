import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { SupabaseClient, Session } from '@supabase/supabase-js'
import { getAuthClient, sessionExpiredEvent } from '../auth'
import { AuthenticationVisibility } from '../authVisibility'
import AppForm from './AppForm'
import '../styles/auth.css'

export default function AuthGate({ children }: { children: ReactNode }) {
  const [client, setClient] = useState<SupabaseClient | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [expired, setExpired] = useState(false)
  const [owner, setOwner] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const heading = useRef<HTMLHeadingElement>(null)
  const pending = useRef(false)
  useEffect(() => {
    let active = true
    let unsubscribe: (() => void) | undefined
    async function start() {
      try {
        const auth = await getAuthClient()
        if (!active) return
        setClient(auth)
        // Subscribe before reading the session so refresh and sign-out cannot race initialization.
        const { data: { subscription } } = auth.auth.onAuthStateChange((event, next) => {
          if (!active) return
          setSession(next)
          if (next) { setOwner(next.user.id); setEmail(next.user.email ?? '') }
          if (event === 'SIGNED_OUT') setOwner(null)
        })
        unsubscribe = () => subscription.unsubscribe()
        const { data, error } = await auth.auth.getSession()
        if (!active) return
        if (error) throw error
        setSession(data.session)
        if (data.session) { setOwner(data.session.user.id); setEmail(data.session.user.email ?? '') }
      } catch {
        if (active) setError('Sign-in is not available. Check the server’s Supabase settings and your connection, then try again.')
      } finally { if (active) setLoading(false) }
    }
    void start()
    function expire() { setExpired(true); setPassword('') }
    window.addEventListener(sessionExpiredEvent, expire)
    return () => { active = false; unsubscribe?.(); window.removeEventListener(sessionExpiredEvent, expire) }
  }, [attempt])
  const signedIn = Boolean(session) && !expired
  useEffect(() => {
    if (!signedIn && !loading) {
      document.title = 'Sign in | MyBudgetPro'
      heading.current?.focus()
    }
  }, [signedIn, loading])

  async function signIn() {
    if (!client || pending.current) return
    pending.current = true
    setBusy(true)
    setError('')
    try {
      const result = await client.auth.signInWithPassword({ email: email.trim(), password })
      if (result.error || !result.data.session) {
        setError(result.error?.status === 400 || result.error?.status === 422
          ? 'Unable to sign in. Check your email and password, then try again.'
          : 'Unable to sign in. Check your connection and try again.')
        return
      }
      setSession(result.data.session)
      setOwner(result.data.session.user.id)
      setExpired(false)
    } catch { setError('Unable to sign in. Check your connection and try again.') }
    finally { setPassword(''); setBusy(false); pending.current = false }
  }

  async function signOut() {
    if (!client || pending.current) return
    pending.current = true
    setBusy(true)
    setError('')
    try {
      const { error } = await client.auth.signOut({ scope: 'local' })
      if (error) { setError('Unable to sign out. Check your connection and try again.'); return }
      setSession(null)
      setOwner(null)
      setExpired(false)
      setPassword('')
    } catch { setError('Unable to sign out. Check your connection and try again.') }
    finally { setBusy(false); pending.current = false }
  }

  return <>
    {owner && <div key={owner} hidden={!signedIn} inert={!signedIn}>
      <div className="auth-session-bar">
        <span>Signed in as <strong>{session?.user.email ?? email}</strong></span>
        <button type="button" className="secondary" data-navigation="sign-out" disabled={busy} onClick={() => void signOut()}>{busy ? 'Signing out…' : 'Sign out'}</button>
        {error && signedIn && <p role="alert">{error}</p>}
      </div>
      <AuthenticationVisibility value={signedIn}>{children}</AuthenticationVisibility>
    </div>}
    {!signedIn && <main className="auth-page" aria-busy={loading || busy}>
      <section className="auth-panel" aria-labelledby="sign-in-title">
        <p className="brand">MyBudgetPro</p>
        <h1 id="sign-in-title" ref={heading} tabIndex={-1}>Sign in to your budget.</h1>
        <p>Sign in to manage your accounts, goals and payments.</p>
        {loading ? <p role="status">Checking your session…</p> : !client ? <>
          <p role="alert">{error}</p>
          <button type="button" onClick={() => { setLoading(true); setError(''); setAttempt(value => value + 1) }}>Try again</button>
        </> : <>
          {expired && <p role="status">Your session has ended. Sign in with the same account to continue where you left off.</p>}
          <AppForm onSubmit={signIn} reserveValidationSpace onInput={() => setError('')} feedback={error && <p role="alert">{error}</p>}>
            <label htmlFor="sign-in-email">Email</label>
            <input id="sign-in-email" name="email" type="email" autoComplete="username" required value={email} onChange={event => setEmail(event.target.value)} disabled={busy} />
            <label htmlFor="sign-in-password">Password</label>
            <div className="auth-password">
              <input id="sign-in-password" name="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={event => setPassword(event.target.value)} disabled={busy} />
              <button type="button" className="secondary" aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword} onClick={() => setShowPassword(value => !value)}>{showPassword ? 'Hide' : 'Show'}</button>
            </div>
            <button type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
          </AppForm>
          <p className="auth-help">Use the account created for you. Contact the app owner if you need access or a password reset.</p>
        </>}
      </section>
    </main>}
  </>
}
