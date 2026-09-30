import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { amount, saveRecord, today } from './api'
import Modal from './Modal'

type Debt = {
  id: number
  name: string
  amount: string
  current_amount: string
  remaining_amount: string
  due_date: string | null
  interest_rate: string | null
  description: string | null
  payments: { id: number; amount: string; paid_on: string; due_date: string | null }[]
}

function DebtForm({ debt, onSave, onCancel, onSavingChange }: {
  debt?: Debt; onSave: (debt: Debt) => void; onCancel?: () => void; onSavingChange?: (saving: boolean) => void
}) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef(false)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending.current) return
    const form = event.currentTarget
    const data = new FormData(form)
    pending.current = true
    setSaving(true)
    onSavingChange?.(true)
    setError('')
    try {
      const saved = await saveRecord<Debt>(debt ? `/api/debts/${debt.id}` : '/api/debts', debt ? 'PUT' : 'POST', {
        name: String(data.get('name')).trim(), amount: data.get('amount'),
        due_date: data.get('due_date') || null,
        interest_rate: data.get('interest_rate') || null,
        description: String(data.get('description')).trim() || null,
        ...(!debt ? { current_amount: data.get('current_amount') } : {}),
      })
      if (!debt) form.reset()
      onSave(saved)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to save debt.')
    } finally { pending.current = false; setSaving(false); onSavingChange?.(false) }
  }
  return <form onSubmit={submit} className={debt ? 'inline-form' : undefined} aria-label={debt ? `Edit ${debt.name}` : 'Add a debt'}>
    <fieldset disabled={saving}>
      <label>Debt name<input name="name" required maxLength={120} placeholder="Student loan" defaultValue={debt?.name} /></label>
      <label>Total debt<input name="amount" type="number" min="0.01" max="999999999999.99" step="0.01" required defaultValue={debt?.amount} placeholder="5000.00" /></label>
      {!debt && <label>Already paid<input name="current_amount" type="number" min="0" max="999999999999.99" step="0.01" required defaultValue="0" /><small>Opening progress from before you started tracking. New payments will have their own history.</small></label>}
      <label>Due date (optional)<input name="due_date" type="date" defaultValue={debt?.due_date ?? ''} /></label>
      <label>Interest rate % (optional)<input name="interest_rate" type="number" min="0" max="100" step="0.01" defaultValue={debt?.interest_rate ?? ''} /><small>For reference only. Interest is not added automatically.</small></label>
      <label>Description (optional)<textarea name="description" maxLength={2000} rows={3} defaultValue={debt?.description ?? ''} /></label>
      <div className="actions"><button type="submit">{saving ? 'Saving…' : debt ? 'Save changes' : 'Add debt'}</button>{onCancel && <button className="secondary" type="button" onClick={onCancel}>Cancel</button>}</div>
    </fieldset>
    {error && <p role="alert">{error}</p>}
  </form>
}

function DebtCard({ debt, onSave }: { debt: Debt; onSave: (debt: Debt) => void }) {
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const pending = useRef(false)
  const paidOff = Number(debt.remaining_amount) === 0
  async function pay(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending.current) return
    const form = event.currentTarget
    const data = new FormData(form)
    pending.current = true
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const updated = await saveRecord<Debt>(`/api/debts/${debt.id}/payments`, 'POST', { amount: data.get('amount'), paid_on: data.get('paid_on') })
      form.reset()
      onSave(updated)
      setNotice(`Payment recorded. ${amount(updated.remaining_amount)} remaining.`)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to record payment.')
    } finally { pending.current = false; setSaving(false) }
  }
  const lastPayment = debt.payments[0]
  return <article>
    <h4>{debt.name}</h4>
    <p><strong>{amount(debt.remaining_amount)}</strong> remaining of {amount(debt.amount)}</p>
    <progress aria-label={`${debt.name} repayment progress`} value={Number(debt.current_amount)} max={Number(debt.amount)} />
    <p>{amount(debt.current_amount)} paid · {Math.round(Number(debt.current_amount) / Number(debt.amount) * 100)}% repaid</p>
    {paidOff ? <p className="status paid">Paid off!</p> : debt.due_date && <p>Due <time dateTime={debt.due_date}>{debt.due_date}</time>{debt.due_date < today() && <span className="status overdue">Overdue</span>}</p>}
    {debt.interest_rate !== null && <p>Interest rate: {debt.interest_rate}% (reference only)</p>}
    {debt.description && <p className="description">{debt.description}</p>}
    <p>{lastPayment ? `Last payment: ${amount(lastPayment.amount)} on ${lastPayment.paid_on}` : 'No payments recorded yet.'}</p>
    {debt.payments.length > 0 && <details><summary>Payment history ({debt.payments.length})</summary><ul className="payment-history">
      {debt.payments.map(payment => <li key={payment.id}><strong>{amount(payment.amount)}</strong> paid on <time dateTime={payment.paid_on}>{payment.paid_on}</time></li>)}
    </ul></details>}
    {editing ? <DebtForm debt={debt} onCancel={() => setEditing(false)} onSave={updated => { onSave(updated); setEditing(false); setNotice('Debt updated.'); }} /> : <>
      {!paidOff && <form className="contribution-form" onSubmit={pay} aria-label={`Record payment for ${debt.name}`}>
        <fieldset disabled={saving}>
          <label>Payment amount<input name="amount" type="number" min="0.01" max={debt.remaining_amount} step="0.01" required placeholder="0.00" /></label>
          <label>Payment date<input name="paid_on" type="date" max={today()} required defaultValue={today()} /></label>
          <button type="submit">{saving ? 'Saving…' : 'Record payment'}</button>
          <small>Records a payment you made; no money is sent.</small>
        </fieldset>
        {error && <p role="alert">{error}</p>}
      </form>}
      <button className="secondary" type="button" disabled={saving} onClick={() => { setEditing(true); setNotice(''); }}>Edit debt</button>
    </>}
    <p role="status">{notice}</p>
  </article>
}

export default function Debts() {
  const [creating, setCreating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [debts, setDebts] = useState<Debt[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await fetch('/api/debts', { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load debts. Check the backend and refresh the page.')
        const saved: Debt[] = await response.json()
        if (!controller.signal.aborted) setDebts(saved)
      } catch (error) {
        if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load debts.')
      } finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load()
    return () => controller.abort()
  }, [])
  return <div className="dashboard-column">
    <div className="list-heading"><div><h2 className="column-heading">Debts</h2><p>A little closer to debt-free.</p></div>
      <button type="button" disabled={loading} onClick={() => setCreating(true)}>Add debt</button></div>
    {creating && <Modal title="Add a debt" busy={saving} onClose={() => setCreating(false)}>
      <DebtForm onSavingChange={setSaving} onSave={saved => { setDebts(previous => [saved, ...previous]); setNotice(`Added ${saved.name}.`); setCreating(false); }} />
    </Modal>}
    <p role="status">{notice}</p>
    <section aria-labelledby="debts-heading" aria-busy={loading}>
      <h3 id="debts-heading">Your debts</h3>
      {loading && <p>Loading debts…</p>}
      {error && <p role="alert">{error}</p>}
      {!loading && !error && debts.length === 0 && <p>No debts yet. Use “Add debt” to track your repayments.</p>}
      {debts.map(debt => <DebtCard key={debt.id} debt={debt} onSave={updated => setDebts(previous => previous.map(item => item.id === updated.id ? updated : item))} />)}
    </section>
  </div>
}
