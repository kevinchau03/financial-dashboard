import { useEffect, useState } from 'react'
import type { Account } from './AccountForm'
import { amount } from '../api'

export default function GoalAccountSelect({ accountId }: { accountId?: number | null }) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await fetch('/api/accounts', { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load accounts. Retry before changing the linked account.')
        const data: Account[] = await response.json()
        if (!controller.signal.aborted) setAccounts(data)
      } catch (error) {
        if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load accounts.')
      } finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load()
    return () => controller.abort()
  }, [retry])
  return <div>
    <label>Keep this goal in an account (optional)
      <select name="account_id" defaultValue={accountId ?? ''} disabled={loading || Boolean(error)}>
        <option value="">No linked account</option>
        {accountId && !accounts.some(account => account.id === accountId) && <option value={accountId}>Linked account</option>}
        {accounts.map(account => <option key={account.id} value={account.id}>{account.name} · {amount(account.available_amount)} unassigned</option>)}
      </select>
    </label>
    <small>Linked goal savings are portions of this account's balance. Assigning existing money does not add a deposit.</small>
    {loading && <p role="status">Loading accounts…</p>}
    {error && <div><p role="alert">{error}</p><button type="button" className="secondary" onClick={() => { setLoading(true); setError(''); setRetry(value => value + 1) }}>Retry accounts</button></div>}
    {!loading && !error && accounts.length === 0 && <p><a href="#/accounts">Add an account</a> to organize goals within it, or save this goal unlinked.</p>}
  </div>
}
