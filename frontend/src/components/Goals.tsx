import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import Modal from './Modal'
import EditForm from './EditForm'
import { amount, saveRecord } from '../api'
import type { Goal } from '../types'

function AddAmountForm({ goal, onSave }: { goal: Goal; onSave: (goal: Goal) => void }) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    const form = event.currentTarget
    const addition = String(new FormData(form).get('amount'))
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const updated = await saveRecord<Goal>(`/api/goals/${goal.id}/contributions`, 'POST', { amount: addition })
      onSave(updated)
      form.reset()
      setNotice(`Added ${amount(addition)}. Now saved: ${amount(updated.current_amount)}.`)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to add amount.')
    } finally { setSaving(false) }
  }

  return <form className="contribution-form" onSubmit={submit} aria-label={`Add savings to ${goal.name}`}>
    <fieldset disabled={saving}>
      <label htmlFor={`contribution-${goal.id}`}>Amount to add</label>
      <div className="contribution-controls">
        <input id={`contribution-${goal.id}`} name="amount" type="number" min="0.01" max="999999999999.99" step="0.01" required placeholder="0.00" />
        <button type="submit">{saving ? 'Adding…' : 'Add amount'}</button>
      </div>
    </fieldset>
    {error && <p role="alert">{error}</p>}
    <p role="status">{notice}</p>
  </form>
}

export default function Goals() {
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const [goals, setGoals] = useState<Goal[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    async function loadGoals() {
      try {
        const response = await fetch('/api/goals', { signal: controller.signal })
        if (!response.ok) throw new Error('Failed to load goals')
        const savedGoals: Goal[] = await response.json()
        if (!controller.signal.aborted) setGoals(savedGoals)
      } catch {
        if (!controller.signal.aborted) setLoadError('Unable to load goals. Check that the backend is running and refresh the page.')
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    void loadGoals()
    return () => controller.abort()
  }, [])

  async function createGoal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    setSaving(true)
    setSaveError('')
    setNotice('')
    try {
      const response = await fetch('/api/goals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: String(data.get('name')).trim(),
          target_amount: data.get('target_amount'),
          current_amount: data.get('current_amount'),
          due_date: data.get('due_date') || null,
          description: String(data.get('description')).trim() || null,
        }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        const message = Array.isArray(body?.detail)
          ? body.detail.map((error: { loc: string[]; msg: string }) => `${error.loc.slice(1).join(' ')}: ${error.msg}`).join('. ')
          : 'Unable to save your goal. Please try again.'
        throw new Error(message)
      }
      const goal: Goal = await response.json()
      setGoals(previous => [goal, ...previous])
      form.reset()
      setNotice(`Created ${goal.name}.`)
      setCreating(false)
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Unable to save your goal.')
    } finally {
      setSaving(false)
    }
  }

  return (
      <div className="dashboard-column">
      <div className="list-heading"><div><h2 className="column-heading">Financial goals</h2><p>Make room for what matters.</p></div>
        <button type="button" onClick={() => { setSaveError(''); setCreating(true); }}>Add goal</button></div>
      {creating && <Modal title="Create a goal" busy={saving} onClose={() => setCreating(false)}>
        <form onSubmit={createGoal}>
          <fieldset disabled={saving}>
            <label>Goal name
              <input name="name" required maxLength={120} placeholder="Emergency fund" />
            </label>
            <div className="amount-fields">
              <label>Target amount
                <input name="target_amount" type="number" min="0.01" max="999999999999.99" step="0.01" required placeholder="5000.00" />
              </label>
              <label>Current amount
                <input name="current_amount" type="number" min="0" max="999999999999.99" step="0.01" required defaultValue="0" />
              </label>
            </div>
            <label>Due date (optional)
              <input name="due_date" type="date" />
            </label>
            <label>Description (optional)
              <textarea name="description" maxLength={2000} rows={3} />
            </label>
            <button type="submit" disabled={loading}>{saving ? 'Saving…' : 'Create goal'}</button>
          </fieldset>
          {saveError && <p role="alert">{saveError}</p>}
        </form>
      </Modal>}
      <p role="status">{notice}</p>
      <section aria-labelledby="goals-heading" aria-busy={loading}>
        <h3 id="goals-heading">Your goals</h3>
        {loading && <p>Loading goals…</p>}
        {loadError && <p role="alert">{loadError}</p>}
        {!loading && !loadError && goals.length === 0 && <p>No goals yet. Use “Add goal” to start saving for something.</p>}
        <div className="goals">
          {goals.map(goal => (
            <article key={goal.id}>
              <h4>{goal.name}</h4>
              <p><strong>{amount(goal.current_amount)}</strong> saved of {amount(goal.target_amount)}</p>
              <progress aria-label={`${goal.name} progress`} value={Math.min(Number(goal.current_amount), Number(goal.target_amount))} max={Number(goal.target_amount)} />
              {goal.due_date && <p>Due <time dateTime={goal.due_date}>{goal.due_date}</time></p>}
              {goal.description && <p className="description">{goal.description}</p>}
              <p>{Math.round(Number(goal.current_amount) / Number(goal.target_amount) * 100)}% saved{Number(goal.current_amount) >= Number(goal.target_amount) ? ' · Goal reached!' : ` · ${amount(String(Number(goal.target_amount) - Number(goal.current_amount)))} to go`}</p>
              {editing === goal.id ? <EditForm item={goal} kind="goals" onCancel={() => setEditing(null)} onSave={updated => {
                setGoals(previous => previous.map(item => item.id === updated.id ? updated as Goal : item))
                setEditing(null)
                setNotice(`Updated ${updated.name}.`)
              }} /> : <>
                <AddAmountForm goal={goal} onSave={updated => setGoals(previous => previous.map(item => item.id === updated.id ? updated : item))} />
                <button className="secondary" type="button" disabled={editing !== null} onClick={() => setEditing(goal.id)}>Edit goal</button>
              </>}
            </article>
          ))}
        </div>
      </section>
      </div>
  )
}

