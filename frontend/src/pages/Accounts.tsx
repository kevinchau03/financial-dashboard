import { useEffect, useState } from 'react'
import AccountForm from '../components/AccountForm'
import type { Account } from '../components/AccountForm'
import Modal from '../components/Modal'
import Notice from '../components/Notice'
import useNotice from '../hooks/useNotice'
import { amount } from '../api'

export default function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [editing, setEditing] = useState<Account | 'new' | null>(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useNotice()
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch('/api/accounts', { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load accounts.')
        const data: Account[] = await response.json()
        if (!controller.signal.aborted) setAccounts(data)
      } catch (error) { if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load accounts.') }
      finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load()
    return () => controller.abort()
  }, [attempt])
  return <div className="accounts-page">
    <div className="page-intro list-heading"><div><h1>Your accounts</h1><p>A simple view of where your money lives.</p></div><button type="button" disabled={loading || !!error} onClick={() => setEditing('new')}>Add account</button></div>
    <p className="wrapped-intro">Manually tracked balances. These are separate from your budget goals and statement imports; changes here do not move or allocate money.</p>
    <Notice message={notice} />
    {loading && <p role="status">Loading accounts…</p>}
    {error && <div><p role="alert">{error}</p><button type="button" onClick={() => setAttempt(previous => previous + 1)}>Retry</button></div>}
    {!loading && !error && accounts.length === 0 && <section><h2>Start with one account</h2><p>Add your savings, chequing, TFSA, or FHSA and its current balance. Update it whenever you check your bank statement.</p><button type="button" onClick={() => setEditing('new')}>Add your first account</button></section>}
    {!loading && !error && <div className="account-grid">{accounts.map(account => <section key={account.id}>
      <p className="brand">{account.account_type}</p><h2>{account.name}</h2><p className="stat-value">{amount(account.balance)}</p>
      <button type="button" className="secondary" onClick={() => setEditing(account)} aria-label={`Update ${account.name}`}>Update account</button>
    </section>)}</div>}
    {editing && <Modal title={editing === 'new' ? 'Add an account' : 'Update account'} busy={busy} onClose={() => setEditing(null)}>
      <AccountForm account={editing === 'new' ? undefined : editing} onBusy={setBusy} onSave={saved => {
        setAccounts(previous => previous.some(account => account.id === saved.id) ? previous.map(account => account.id === saved.id ? saved : account) : [saved, ...previous])
        setEditing(null)
        setNotice(`Saved ${saved.name}.`)
      }} />
    </Modal>}
  </div>
}
