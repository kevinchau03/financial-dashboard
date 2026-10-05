import AppForm from './AppForm'
import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { saveRecord } from '../api'

export type Account = { id: number; name: string; account_type: string; balance: string }

export default function AccountForm({ account, onSave, onBusy }: {
  account?: Account; onSave: (account: Account) => void; onBusy: (busy: boolean) => void
}) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef(false)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending.current) return
    const data = new FormData(event.currentTarget)
    pending.current = true
    setSaving(true)
    onBusy(true)
    setError('')
    try {
      const saved = await saveRecord<Account>(account ? `/api/accounts/${account.id}` : '/api/accounts', account ? 'PUT' : 'POST', {
        name: String(data.get('name')).trim(), account_type: data.get('account_type'), balance: data.get('balance'),
      })
      onSave(saved)
    } catch (error) { setError(error instanceof Error ? error.message : 'Unable to save account.') }
    finally { pending.current = false; setSaving(false); onBusy(false) }
  }
  return <AppForm onSubmit={submit}>
    <fieldset disabled={saving}>
      <label>Account name<input name="name" required maxLength={120} defaultValue={account?.name} placeholder="Everyday chequing" /></label>
      <label>Account type<select name="account_type" defaultValue={account?.account_type ?? 'Savings'}>
        {['Savings', 'Chequing', 'TFSA', 'FHSA', 'RRSP', 'Other'].map(type => <option key={type}>{type}</option>)}
      </select></label>
      <label>Current balance<input name="balance" type="number" step="0.01" min="-999999999999.99" max="999999999999.99" required defaultValue={account?.balance ?? '0'} /></label>
      <small>Enter the current balance manually. Negative balances are allowed.</small>
      <button type="submit">{saving ? 'Saving…' : 'Save account'}</button>
    </fieldset>
    {error && <p role="alert">{error}</p>}
  </AppForm>
}

