import Debts from './Debts'
import Modal from './Modal'
import { amount, today, saveRecord } from './api'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type Goal = {
  id: number
  name: string
  target_amount: string
  current_amount: string
  due_date: string | null
  description: string | null
}

type Bill = {
  id: number
  name: string
  amount: string
  due_date: string | null
  recurring: boolean
  description: string | null
  is_paid: boolean
  payments: { id: number; amount: string; paid_on: string; due_date: string | null }[]
}

function EditForm({ item, kind, onSave, onCancel }: {
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
  return <form className="inline-form" onSubmit={submit} aria-label={`Edit ${item.name}`}>
    <fieldset disabled={saving}>
      <label>Name<input name="name" required maxLength={120} defaultValue={item.name} autoFocus /></label>
      {'target_amount' in item ? <div className="amount-fields">
        <label>Target amount<input name="target_amount" type="number" min="0.01" max="999999999999.99" step="0.01" required defaultValue={item.target_amount} /></label>
      </div> : <>
        <label>Amount<input name="amount" type="number" min="0.01" max="999999999999.99" step="0.01" required defaultValue={item.amount} /></label>
        <label className="checkbox-label"><input name="recurring" type="checkbox" defaultChecked={item.recurring} />Recurring bill</label>
      </>}
      <label>Due date (optional)<input name="due_date" type="date" defaultValue={item.due_date ?? ''} /></label>
      {'is_paid' in item && item.is_paid && <small>Changing the due date schedules a new unpaid bill. Previous payments stay in your history.</small>}
      <label>Description (optional)<textarea name="description" maxLength={2000} rows={3} defaultValue={item.description ?? ''} /></label>
      <div className="actions"><button type="submit">{saving ? 'Saving…' : 'Save changes'}</button><button className="secondary" type="button" onClick={onCancel}>Cancel</button></div>
    </fieldset>
    {error && <p role="alert">{error}</p>}
  </form>
}

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

function PaymentForm({ bill, onSave, onCancel }: { bill: Bill; onSave: (bill: Bill) => void; onCancel: () => void }) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    setSaving(true)
    setError('')
    try {
      onSave(await saveRecord<Bill>(`/api/bills/${bill.id}/payments`, 'POST', {
        amount: data.get('amount'), paid_on: data.get('paid_on'), next_due_date: data.get('next_due_date') || null,
      }))
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to record payment.')
    } finally { setSaving(false) }
  }
  return <form className="inline-form" onSubmit={submit} aria-label={`Record payment for ${bill.name}`}>
    <fieldset disabled={saving}>
      <label>Amount paid<input name="amount" type="number" min="0.01" max="999999999999.99" step="0.01" required defaultValue={bill.amount} autoFocus /></label>
      <label>Payment date<input name="paid_on" type="date" required max={today()} defaultValue={today()} /></label>
      {bill.recurring && <label>Next due date (optional)<input name="next_due_date" type="date" /><small>Set the next occurrence, or leave blank to mark this bill paid with no upcoming date.</small></label>}
      <small>This marks the current bill as fully paid, even if the amount differs. It records the payment without sending money.</small>
      <div className="actions"><button type="submit">{saving ? 'Saving…' : 'Save payment'}</button><button className="secondary" type="button" onClick={onCancel}>Cancel</button></div>
    </fieldset>
    {error && <p role="alert">{error}</p>}
  </form>
}

function Bills() {
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const [paying, setPaying] = useState<number | null>(null)
  const [bills, setBills] = useState<Bill[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    async function loadBills() {
      try {
        const response = await fetch('/api/bills', { signal: controller.signal })
        if (!response.ok) throw new Error('Failed to load bills')
        const savedBills: Bill[] = await response.json()
        if (!controller.signal.aborted) setBills(savedBills)
      } catch {
        if (!controller.signal.aborted) setLoadError('Unable to load bills. Check that the backend is running and refresh the page.')
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    void loadBills()
    return () => controller.abort()
  }, [])

  async function createBill(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    setSaving(true)
    setSaveError('')
    setNotice('')
    try {
      const response = await fetch('/api/bills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: String(data.get('name')).trim(),
          amount: data.get('amount'),
          due_date: data.get('due_date') || null,
          recurring: data.get('recurring') === 'on',
          description: String(data.get('description')).trim() || null,
        }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        const message = Array.isArray(body?.detail)
          ? body.detail.map((error: { loc: string[]; msg: string }) => `${error.loc.slice(1).join(' ')}: ${error.msg}`).join('. ')
          : 'Unable to save your bill. Please try again.'
        throw new Error(message)
      }
      const bill: Bill = await response.json()
      setBills(previous => [bill, ...previous])
      form.reset()
      setNotice(`Created ${bill.name}.`)
      setCreating(false)
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Unable to save your bill.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <aside className="dashboard-column bills-sidebar" aria-label="Bill reminders">
      <div className="list-heading"><div><h2 className="column-heading">Bill reminders</h2><p>Keep upcoming payments in view.</p></div>
        <button className="secondary" type="button" onClick={() => { setSaveError(''); setCreating(true); }}>Add bill</button></div>
      {creating && <Modal title="Add a bill" busy={saving} onClose={() => setCreating(false)}>
        <form onSubmit={createBill}>
          <fieldset disabled={saving}>
            <label>Bill name
              <input name="name" required maxLength={120} placeholder="Internet" />
            </label>
            <label>Amount
              <input name="amount" type="number" min="0.01" max="999999999999.99" step="0.01" required placeholder="65.00" />
            </label>
            <label>Due date (optional)
              <input name="due_date" type="date" />
            </label>
            <label className="checkbox-label">
              <input name="recurring" type="checkbox" /> Recurring bill
            </label>
            <label>Description (optional)
              <textarea name="description" maxLength={2000} rows={3} />
            </label>
            <button type="submit" disabled={loading}>{saving ? 'Saving…' : 'Add bill'}</button>
          </fieldset>
          {saveError && <p role="alert">{saveError}</p>}
        </form>
      </Modal>}
      <p role="status">{notice}</p>
      <section aria-labelledby="bills-heading" aria-busy={loading}>
        <h3 id="bills-heading">Your bills</h3>
        {loading && <p>Loading bills…</p>}
        {loadError && <p role="alert">{loadError}</p>}
        {!loading && !loadError && bills.length === 0 && <p>No bills yet. Use “Add bill” to set up a reminder.</p>}
        <div className="bills">
          {[...bills].sort((a, b) => Number(a.is_paid) - Number(b.is_paid) || (a.due_date ?? '9999').localeCompare(b.due_date ?? '9999')).map(bill => (
            <article key={bill.id}>
              <div className="bill-title"><h4>{bill.name}</h4><strong>{amount(bill.amount)}</strong></div>
              <p className="bill-meta">{bill.recurring ? 'Recurring' : 'One-time'} · {bill.due_date ? <>Due <time dateTime={bill.due_date}>{bill.due_date}</time></> : 'No due date'}</p>
              <p><span className={`status ${bill.is_paid ? 'paid' : bill.due_date && bill.due_date < today() ? 'overdue' : ''}`}>
                {bill.is_paid ? 'Paid' : bill.due_date && bill.due_date < today() ? 'Overdue' : 'Unpaid'}
              </span></p>
              <details className="bill-details"><summary>Details & payment history</summary>
              {bill.description && <p className="description">{bill.description}</p>}
              <p>{bill.payments.length ? `Last payment: ${amount(bill.payments[0].amount)} on ${bill.payments[0].paid_on}` : 'No payments recorded yet.'}</p>
              {bill.payments.length > 0 && <details><summary>Payment history ({bill.payments.length})</summary><ul className="payment-history">
                {bill.payments.map(payment => <li key={payment.id}><strong>{amount(payment.amount)}</strong> paid on <time dateTime={payment.paid_on}>{payment.paid_on}</time>{payment.due_date && <> · for bill due {payment.due_date}</>}</li>)}
              </ul></details>}
              </details>
              {editing === bill.id ? <EditForm item={bill} kind="bills" onCancel={() => setEditing(null)} onSave={updated => {
                setBills(previous => previous.map(item => item.id === updated.id ? updated as Bill : item))
                setEditing(null)
                setNotice(`Updated ${updated.name}.`)
              }} /> : paying === bill.id ? <PaymentForm bill={bill} onCancel={() => setPaying(null)} onSave={updated => {
                setBills(previous => previous.map(item => item.id === updated.id ? updated : item))
                setPaying(null)
                setNotice(`Payment recorded for ${updated.name}.`)
              }} /> : <div className="actions">
                <button className="secondary" type="button" disabled={editing !== null || paying !== null} onClick={() => setEditing(bill.id)}>Edit bill</button>
                {!bill.is_paid && <button type="button" disabled={editing !== null || paying !== null} onClick={() => setPaying(bill.id)}>Record payment</button>}
              </div>}
            </article>
          ))}
        </div>
      </section>
    </aside>
  )
}

function App() {
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
    <main>
      <header>
        <p className="brand">MyBudgetPro</p>
        <h1>Financial planning made easy.</h1>
        <p>Keep your goals, bills, and debts in one place.</p>
      </header>
      <div className="dashboard">
      <div className="primary-workspace">
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
      <Debts />
      </div>
      <Bills />
      </div>
    </main>
  )
}

export default App

