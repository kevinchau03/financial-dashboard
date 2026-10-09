import AppForm from './AppForm'
import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { Goal } from '../types'
import { saveRecord } from '../api'
import { cents } from '../goalPlanning'
import Notice from './Notice'
import useNotice from '../hooks/useNotice'

export default function GoalFunding({ goal, onSave }: {
  goal: Goal; onSave: (goal: Goal) => void
}) {
  const [saving, setSaving] = useState(false)
  const [value, setValue] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useNotice()
  const pending = useRef(false)
  const limit = 99999999999999 - cents(goal.current_amount)
  const remaining = Math.max(0, cents(goal.target_amount) - cents(goal.current_amount))
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending.current) return
    pending.current = true
    setSaving(true)
    setError('')
    try {
      const updated = await saveRecord<Goal>(`/api/goals/${goal.id}/contributions`, 'POST', { amount: value })
      onSave(updated)
      setValue('')
      setNotice('Savings added.')
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to update savings.')
    } finally { pending.current = false; setSaving(false) }
  }
  return <AppForm className="contribution-form" onSubmit={submit} aria-label={`Update savings for ${goal.name}`}>
    <fieldset disabled={saving}>

      <label htmlFor={`funding-${goal.id}`}>{goal.account_id ? 'Assign account money' : 'Add new savings'}</label>
      <small>{goal.account_id ? 'Earmark money already in the linked account. Its balance stays unchanged.' : 'Record money you have actually saved toward this goal.'}</small>
      <div className="contribution-controls">
        <input id={`funding-${goal.id}`} type="number" required min="0.01" max={Math.max(0, limit / 100)} step="0.01" value={value} onChange={event => setValue(event.target.value)} placeholder="0.00" disabled={limit <= 0} />
        <button type="submit" disabled={limit <= 0}>{saving ? 'Saving…' : goal.account_id ? 'Assign amount' : 'Add savings'}</button>
      </div>
      {remaining > 0 && limit > 0 && <button type="button" className="secondary" onClick={() => setValue((Math.min(remaining, limit) / 100).toFixed(2))}>
        Fill remaining target
      </button>}
    </fieldset>
    {error && <p role="alert">{error}</p>}
    <Notice message={notice} />
  </AppForm>
}



