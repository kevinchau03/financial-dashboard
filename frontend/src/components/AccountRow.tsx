import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { Account } from './AccountForm'
import AppForm from './AppForm'
import { amount, saveRecord } from '../api'

export default function AccountRow({ account, onSave, onEdit }: {
  account: Account; onSave: (account: Account) => void; onEdit: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef(false)
  const trigger = useRef<HTMLButtonElement>(null)
  const cancel = useRef<HTMLButtonElement>(null)
  const input = useRef<HTMLInputElement>(null)

  function close() {
    setEditing(false)
    setError('')
    requestAnimationFrame(() => trigger.current?.focus())
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending.current) return
    const balance = new FormData(event.currentTarget).get('balance')
    pending.current = true
    setSaving(true)
    setError('')
    try {
      const saved = await saveRecord<Account>(`/api/accounts/${account.id}`, 'PUT', {
        name: account.name, account_type: account.account_type, balance,
      })
      onSave(saved)
      close()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to save balance. Please try again.')
      requestAnimationFrame(() => input.current?.focus())
    } finally { pending.current = false; setSaving(false) }
  }

  return <li className="account-row">
    <div className="account-identity"><h2>{account.name}</h2><span className="account-type">{account.account_type}</span></div>
    <div className="account-figure"><span>Allocated</span><strong>{amount(account.earmarked_amount)}</strong></div>
    <div className="account-figure"><span>Unassigned</span><strong>{amount(account.available_amount)}</strong></div>
    <div className="account-balance">
      {editing ? <AppForm className="account-balance-form" aria-label={`Update balance for ${account.name}`} onSubmit={submit}
        onKeyDown={event => {
          if (event.key === 'Enter' && event.nativeEvent.isComposing) event.preventDefault()
          if (event.key === 'Escape' && !event.nativeEvent.isComposing && !pending.current) {
            event.preventDefault()
            cancel.current?.click()
          }
        }}>
        <fieldset disabled={saving}>
          <label>Current balance<input ref={input} name="balance" type="number" inputMode="decimal" step="0.01" min="-999999999999.99" max="999999999999.99" required
            defaultValue={account.balance} autoFocus onFocus={event => event.currentTarget.select()} /></label>
          <div className="account-balance-actions"><button type="submit" aria-busy={saving}>{saving ? 'Saving…' : 'Save'}</button><button ref={cancel} type="button" className="secondary" onClick={close}>Cancel</button></div>
        </fieldset>
        {error && <p role="alert">{error}</p>}
      </AppForm> : <button ref={trigger} type="button" className="balance-edit-button" aria-label={`Edit balance for ${account.name}, ${amount(account.balance)}`}
        onClick={() => setEditing(true)}>
        <span className="balance-label">Current balance</span>
        <span className="balance-value">{amount(account.balance)}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m16 3 5 5-12 12-6 1 1-6Z M14 5l5 5" /></svg></span>
        <span className="balance-edit-hint">Edit balance</span>
      </button>}
    </div>
    <div className="account-row-actions"><button type="button" className="account-details-button" disabled={editing} onClick={onEdit} aria-label={`Edit details for ${account.name}`}>Edit details</button></div>
    {account.goal_summary.length > 0 && <details className="account-linked-goals"><summary>{account.goal_summary.length} linked {account.goal_summary.length === 1 ? 'goal' : 'goals'}</summary>
      <ul>{account.goal_summary.map(goal => <li key={goal.id}><span>{goal.name}</span><span>{amount(goal.current_amount)} of {amount(goal.target_amount)}</span></li>)}</ul>
      <a href="#/budget">Manage goals</a>
    </details>}
  </li>
}
