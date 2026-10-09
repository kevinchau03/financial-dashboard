import AutoTextarea from './AutoTextarea'
import EmptyState from './EmptyState'
import AppForm from './AppForm'
import Notice from './Notice'
import DeleteItem from './DeleteItem'
import useNotice from '../hooks/useNotice'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import Modal from './Modal'
import CollapsibleItem from './CollapsibleItem'
import EditForm from './EditForm'
import { amount } from '../api'
import GoalFunding from './GoalFunding'
import GoalPlan from './GoalPlan'
import GoalAccountSelect from './GoalAccountSelect'
import type { Goal } from '../types'

export default function Goals({ onSavingsChange = () => undefined, revision = 0 }: { onSavingsChange?: () => void; revision?: number }) {
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const [goals, setGoals] = useState<Goal[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useNotice()

  useEffect(() => {
    const controller = new AbortController()
    async function loadGoals() {
      setLoadError('')
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
  }, [revision])

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
          account_id: data.get('account_id') ? Number(data.get('account_id')) : null,
          due_date: data.get('due_date') || null,
          description: String(data.get('description')).trim() || null,
        }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        const message = Array.isArray(body?.detail)
          ? body.detail.map((error: { loc: string[]; msg: string }) => `${error.loc.slice(1).join(' ')}: ${error.msg}`).join('. ')
          : typeof body?.detail === 'string' ? body.detail : 'Unable to save your goal. Please try again.'
        throw new Error(message)
      }
      const goal: Goal = await response.json()
      setGoals(previous => [goal, ...previous])
      onSavingsChange()
      form.reset()
      setNotice(`Created ${goal.name}.`)
      setCreating(false)
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Unable to save your goal.')
    } finally {
      setSaving(false)
    }
  }

  function renderGoal(goal: Goal) {
    return (
            <CollapsibleItem key={goal.id} title={goal.name}
              summary={<><strong>{amount(goal.current_amount)}</strong> saved of {amount(goal.target_amount)}<small className="goal-account-label">{goal.account_name ? `Account: ${goal.account_name}` : 'No linked account'}</small></>}
              progress={Number(goal.current_amount)} target={Number(goal.target_amount)} progressLabel={`${goal.name} progress`}>
              {goal.due_date && <p>Due <time dateTime={goal.due_date}>{goal.due_date}</time></p>}
              {goal.account_name && <p>Kept in <strong>{goal.account_name}</strong> · earmarked from its balance</p>}
              <GoalPlan goal={goal} />
              {goal.description && <p className="description">{goal.description}</p>}
              <p>{Math.round(Number(goal.current_amount) / Number(goal.target_amount) * 100)}% saved{Number(goal.current_amount) >= Number(goal.target_amount) ? ' · Goal reached!' : ` · ${amount(String(Number(goal.target_amount) - Number(goal.current_amount)))} to go`}</p>
              {editing === goal.id ? <EditForm item={goal} kind="goals" onCancel={() => setEditing(null)} onSave={updated => {
                setGoals(previous => previous.map(item => item.id === updated.id ? updated as Goal : item))
                setEditing(null)
                setNotice(`Updated ${updated.name}.`)
              }} /> : <>
                <GoalFunding goal={goal} onSave={updated => {
                  setGoals(previous => previous.map(item => item.id === updated.id ? updated : item))
                  onSavingsChange()
                }} />
                <button className="secondary" type="button" disabled={editing !== null} onClick={() => setEditing(goal.id)}>Edit goal</button>
                <DeleteItem kind="goals" id={goal.id} name={goal.name} disabled={editing !== null} onDelete={() => {
                  setGoals(previous => previous.filter(item => item.id !== goal.id))
                  onSavingsChange()
                  setNotice(`Deleted ${goal.name}.`)
                }} />
              </>}

            </CollapsibleItem>
  ) }

  return (
      <div className="dashboard-column" data-tone="leaf">
      <div className="list-heading"><div><h2 className="column-heading">Goals</h2><p>Choose a target, make a saving plan, and give your savings a purpose.</p></div>
        <button type="button" onClick={() => { setSaveError(''); setCreating(true); }}>Add goal</button></div>
      {creating && <Modal title="Create a goal" busy={saving} onClose={() => setCreating(false)}>
        <AppForm onSubmit={createGoal}>
          <fieldset disabled={saving}>
            <label>What are you saving for?
              <input name="name" required maxLength={120} placeholder="Emergency fund, vacation…" />
            </label>
            <GoalAccountSelect />
            <div className="amount-fields">
              <label>Target amount
                <input name="target_amount" type="number" min="0.01" max="999999999999.99" step="0.01" required placeholder="5000.00" />
              </label>
              <label>Current amount
                <input name="current_amount" type="number" min="0" max="999999999999.99" step="0.01" required defaultValue="0" />
              </label>
            </div>
            <label>When would you like to reach it? (optional)
              <input name="due_date" type="date" />
            </label>
            <label>Why this matters / how you will save (optional)
              <AutoTextarea name="description" maxLength={2000} rows={3} placeholder="For example: set aside part of each paycheque for a summer trip." />
            </label>
            <button type="submit" disabled={loading}>{saving ? 'Saving…' : 'Create goal'}</button>
          </fieldset>
          {saveError && <p role="alert">{saveError}</p>}
        </AppForm>
      </Modal>}
      <Notice message={notice} />
      <section aria-labelledby="goals-heading" aria-busy={loading}>
        <h3 className="sr-only" id="goals-heading">Your goals</h3>
        {loading && <p>Loading goals…</p>}
        {loadError && <p role="alert">{loadError}</p>}
        {!loading && !loadError && goals.length === 0 && <EmptyState title="Start with something that matters" description="A rainy-day fund, a trip, or your next big step. Give it a target and build from there." action="Create your first goal" onAction={() => { setSaveError(''); setCreating(true); }} />}
        <div className="goals">
          {goals.map(renderGoal)}
        </div>
      </section>
      </div>
  )
}
