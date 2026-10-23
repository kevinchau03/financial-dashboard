import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { SupabaseClient, Session } from '@supabase/supabase-js'
import { getAuthClient, sessionExpiredEvent } from '../auth'
import { AuthenticationVisibility } from '../authVisibility'
import AppForm from './AppForm'
import '../styles/auth.css'

export default function AuthGate({ children, path }: { children: (accountPanel: ReactNode, signedIn: boolean) => ReactNode; path: string }) {
  const publicPage = path === '#/' || path === '#/learn'
  const signingUp = path === '#/sign-up'
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
  const [message, setMessage] = useState('')
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
    if (!signedIn && !publicPage) {
      document.title = `${signingUp ? 'Sign up' : 'Sign in'} | MyBudgetPro`
      heading.current?.focus()
    }
    if (signedIn && (path === '#/sign-in' || path === '#/sign-up')) window.location.hash = '#/dashboard'
  }, [signedIn, loading, publicPage, signingUp, path])

  function changeMode() {
    setPassword('')
    setShowPassword(false)
    setError('')
    setMessage('')
  }

  async function signIn() {
    if (!client || pending.current) return
    pending.current = true
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const result = signingUp
        ? await client.auth.signUp({ email: email.trim(), password, options: {
          emailRedirectTo: `${window.location.origin}${window.location.pathname}`,
        } })
        : await client.auth.signInWithPassword({ email: email.trim(), password })
      if (signingUp && !result.error && !result.data.session) {
        setMessage('Check your email for a confirmation link. After confirming, return here to sign in. If you already have an account, sign in instead.')
        return
      }
      if (result.error || !result.data.session) {
        if (signingUp) {
          setError(result.error?.code === 'signup_disabled'
            ? 'Sign-up is currently unavailable. Contact the app owner for access.'
            : result.error?.code === 'weak_password'
              ? 'Choose a stronger password and try again.'
              : result.error?.status === 429
                ? 'Too many attempts. Please wait a few minutes before trying again.'
                : 'Unable to sign up. Try again, or sign in if you already have an account.')
          return
        }
        setError(result.error?.status === 400 || result.error?.status === 422
          ? 'Unable to sign in. Check your email and password, then try again.'
          : 'Unable to sign in. Check your connection and try again.')
        return
      }
      setSession(result.data.session)
      setOwner(result.data.session.user.id)
      setExpired(false)
    } catch { setError(`Unable to ${signingUp ? 'sign up' : 'sign in'}. Check your connection and try again.`) }
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

  const accountPanel = <div className="auth-account-panel" aria-label="Your account" role="region">
    <span className="auth-account-label">Signed in as</span><strong className="auth-account-email">{session?.user.email ?? email}</strong>
    <button type="button" className="secondary" data-navigation="sign-out" disabled={busy} onClick={() => void signOut()}>{busy ? 'Signing out…' : 'Sign out'}</button>
    {error && signedIn && <p role="alert">{error}</p>}
  </div>

  // Public content must render even while session/configuration requests are unavailable.
  if (publicPage) return children(signedIn ? accountPanel : <nav className="auth-guest-actions" aria-label="Account">
    <a href="#/sign-in" onClick={changeMode}>Sign in</a>
    <a className="button-link" href="#/sign-up" onClick={changeMode}>Sign up</a>
  </nav>, signedIn)

  return <>
    {owner && <div key={owner} hidden={!signedIn} inert={!signedIn}>
      <AuthenticationVisibility value={signedIn}>{children(accountPanel, signedIn)}</AuthenticationVisibility>
    </div>}
    {!signedIn && <main className="auth-page" aria-busy={loading || busy}>
      <section className="auth-panel" aria-labelledby="sign-in-title">
        <a className="brand" href="#/" onClick={changeMode}>MyBudgetPro · Home</a>
        <h1 id="sign-in-title" ref={heading} tabIndex={-1}>{signingUp ? 'Create your account.' : 'Sign in to your budget.'}</h1>
        <p>{signingUp ? 'Start keeping track of your accounts, goals and payments.' : 'Sign in to manage your accounts, goals and payments.'}</p>
        {loading ? <p role="status">Checking your session…</p> : !client ? <>
          <p role="alert">{error}</p>
          <button type="button" onClick={() => { setLoading(true); setError(''); setAttempt(value => value + 1) }}>Try again</button>
        </> : <>
          {expired && !signingUp && <p role="status">Your session has ended. Sign in with the same account to continue where you left off.</p>}
          <AppForm key={signingUp ? 'sign-up' : 'sign-in'} onSubmit={signIn} reserveValidationSpace onInput={() => setError('')} feedback={<>{error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}</>}>
            <label htmlFor="sign-in-email">Email</label>
            <input id="sign-in-email" name="email" type="email" autoComplete="username" required value={email} onChange={event => setEmail(event.target.value)} disabled={busy} />
            <label htmlFor="sign-in-password">Password</label>
            <div className="auth-password">
              <input id="sign-in-password" name="password" type={showPassword ? 'text' : 'password'} autoComplete={signingUp ? 'new-password' : 'current-password'} minLength={signingUp ? 12 : undefined} aria-describedby={signingUp ? 'password-guidance' : undefined} required value={password} onChange={event => setPassword(event.target.value)} disabled={busy} />
              <button type="button" className="secondary" aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword} onClick={() => setShowPassword(value => !value)}>{showPassword ? 'Hide' : 'Show'}</button>
            </div>
            {signingUp && <p id="password-guidance" className="auth-help">Use at least 12 characters. A unique passphrase works well.</p>}
            <button type="submit" disabled={busy}>{busy ? (signingUp ? 'Signing up…' : 'Signing in…') : (signingUp ? 'Sign up' : 'Sign in')}</button>
          </AppForm>
          <p className="auth-help">{signingUp ? 'Already have an account? ' : 'New to MyBudgetPro? '}<a href={signingUp ? '#/sign-in' : '#/sign-up'} onClick={changeMode}>{signingUp ? 'Sign in' : 'Sign up'}</a></p>
          {!signingUp && <p className="auth-help">Contact the app owner if you need a password reset.</p>}
        </>}
      </section>
    </main>}
  </>
}
