import AutoTextarea from './AutoTextarea'
import AppForm from './AppForm'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { saveRecord } from '../api'
import type { Goal, Bill } from '../types'

export default function EditForm({ item, kind, onSave, onCancel }: {
  item: Goal | Bill; kind: 'goals' | 'bills'; onSave: (item: Goal | Bill) => void; onCancel: () => void
}) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    setSaving(true)
    setError('')
    try {
      const updated = await saveRecord<Goal | Bill>(`/api/${kind}/${item.id}`, 'PUT', {
        name: String(data.get('name')).trim(),
        due_date: data.get('due_date') || null,
        description: String(data.get('description')).trim() || null,
        ...(kind === 'goals' ? { target_amount: data.get('target_amount') }
          : { amount: data.get('amount'), recurring: data.get('recurring') === 'on' }),
      })
      onSave(updated)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to save changes.')
    } finally { setSaving(false) }
  }
  return <AppForm className="inline-form" onSubmit={submit} aria-label={`Edit ${item.name}`}>
    <fieldset disabled={saving}>
      <label>Name<input name="name" required maxLength={120} defaultValue={item.name} autoFocus /></label>
      {'target_amount' in item ? <div className="amount-fields">
        <label>Target amount<input name="target_amount" type="number" min="0.01" max="999999999999.99" step="0.01" required defaultValue={item.target_amount} /></label>
      </div> : <>
        <label>Amount<input name="amount" type="number" min="0.01" max="999999999999.99" step="0.01" required defaultValue={item.amount} /></label>
        <label className="checkbox-label"><input name="recurring" type="checkbox" defaultChecked={item.recurring} />Repeat monthly</label>
      </>}
      <label>{kind === 'bills' ? 'Due date (required for monthly bills)' : 'Target date (optional)'}<input name="due_date" type="date" defaultValue={item.due_date ?? ''} /></label>
      {'is_paid' in item && item.is_paid && <small>Changing the due date schedules a new unpaid bill. Previous payments stay in your history.</small>}
      <label>Description (optional)<AutoTextarea name="description" maxLength={2000} rows={3} defaultValue={item.description ?? ''} /></label>
      <div className="actions"><button type="submit">{saving ? 'Saving…' : 'Save changes'}</button><button className="secondary" type="button" onClick={onCancel}>Cancel</button></div>
    </fieldset>
    {error && <p role="alert">{error}</p>}
  </AppForm>
}





