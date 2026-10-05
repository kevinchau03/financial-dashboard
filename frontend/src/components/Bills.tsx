import AutoTextarea from './AutoTextarea'
import EmptyState from './EmptyState'
import AppForm from './AppForm'
import Notice from './Notice'
import DeleteItem from './DeleteItem'
import useNotice from '../hooks/useNotice'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import Modal from './Modal'
import BillItem from './BillItem'
import EditForm from './EditForm'
import { amount, today, saveRecord } from '../api'
import type { Bill } from '../types'
import { billStatus } from '../billStatus'

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
        amount: data.get('amount'), paid_on: data.get('paid_on'),
      }))
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to record payment.')
    } finally { setSaving(false) }
  }
  return <AppForm className="inline-form" onSubmit={submit} aria-label={`Record payment for ${bill.name}`}>
    <fieldset disabled={saving}>
      <label>Amount paid<input name="amount" type="number" min="0.01" max="999999999999.99" step="0.01" required defaultValue={bill.amount} autoFocus /></label>
      <label>Payment date<input name="paid_on" type="date" required max={today()} defaultValue={today()} /></label>
      {bill.recurring && <small>Recording this payment moves the due date forward one month. Shorter months use their last day.</small>}
      <small>This marks the current bill as fully paid, even if the amount differs. It records the payment without sending money.</small>
      <div className="actions"><button type="submit">{saving ? 'Saving…' : 'Save payment'}</button><button className="secondary" type="button" onClick={onCancel}>Cancel</button></div>
    </fieldset>
    {error && <p role="alert">{error}</p>}
  </AppForm>
}

export default function Bills({ onChange }: { onChange: () => void }) {
  const [currentDate, setCurrentDate] = useState(today)
  useEffect(() => {
    const refreshDate = () => setCurrentDate(today())
    const timer = window.setInterval(refreshDate, 30000)
    window.addEventListener('focus', refreshDate)
    return () => { window.clearInterval(timer); window.removeEventListener('focus', refreshDate) }
  }, [])
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const [paying, setPaying] = useState<number | null>(null)
  const [bills, setBills] = useState<Bill[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useNotice()

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
          : typeof body?.detail === 'string' ? body.detail : 'Unable to save your bill. Please try again.'
        throw new Error(message)
      }
      const bill: Bill = await response.json()
      setBills(previous => [bill, ...previous])
      onChange()
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
        <AppForm onSubmit={createBill}>
          <fieldset disabled={saving}>
            <label>Bill name
              <input name="name" required maxLength={120} placeholder="Internet" />
            </label>
            <label>Amount
              <input name="amount" type="number" min="0.01" max="999999999999.99" step="0.01" required placeholder="65.00" />
            </label>
            <label>Due date (required for monthly bills)
              <input name="due_date" type="date" />
            </label>
            <label className="checkbox-label">
              <input name="recurring" type="checkbox" /> Repeat monthly
            </label>
            <label>Description (optional)
              <AutoTextarea name="description" maxLength={2000} rows={3} />
            </label>
            <button type="submit" disabled={loading}>{saving ? 'Saving…' : 'Add bill'}</button>
          </fieldset>
          {saveError && <p role="alert">{saveError}</p>}
        </AppForm>
      </Modal>}
      <Notice message={notice} />
      <section aria-labelledby="bills-heading" aria-busy={loading}>
        <h3 className="sr-only" id="bills-heading">Your bills</h3>
        {loading && <p>Loading bills…</p>}
        {loadError && <p role="alert">{loadError}</p>}
        {!loading && !loadError && bills.length === 0 && <EmptyState title="Stay one step ahead" description="Keep due dates here so upcoming bills are easy to remember." action="Add your first bill" onAction={() => { setSaveError('' ); setCreating(true); }} />}
        <div className="bills">
          {[...bills].sort((a, b) => Number(billStatus(a, currentDate) === 'paid') - Number(billStatus(b, currentDate) === 'paid') || (a.due_date ?? '9999').localeCompare(b.due_date ?? '9999')).map(bill => (
            <BillItem key={bill.id} bill={bill} currentDate={currentDate} active={editing === bill.id || paying === bill.id}>
              {bill.description && <p className="description">{bill.description}</p>}
              <p>{bill.payments.length ? `Last payment: ${amount(bill.payments[0].amount)} on ${bill.payments[0].paid_on}` : 'No payments recorded yet.'}</p>
              {bill.payments.length > 0 && <details><summary>Payment history ({bill.payments.length})</summary><ul className="payment-history">
                {bill.payments.map(payment => <li key={payment.id}><strong>{amount(payment.amount)}</strong> paid on <time dateTime={payment.paid_on}>{payment.paid_on}</time>{payment.due_date && <> · for bill due {payment.due_date}</>}</li>)}
              </ul></details>}
              {editing === bill.id ? <EditForm item={bill} kind="bills" onCancel={() => setEditing(null)} onSave={updated => {
                setBills(previous => previous.map(item => item.id === updated.id ? updated as Bill : item))
                onChange()
                setEditing(null)
                setNotice(`Updated ${updated.name}.`)
              }} /> : paying === bill.id ? <PaymentForm bill={bill} onCancel={() => setPaying(null)} onSave={updated => {
                setBills(previous => previous.map(item => item.id === updated.id ? updated : item))
                onChange()
                setPaying(null)
                setNotice(`Payment recorded for ${updated.name}.`)
              }} /> : <div className="actions">
                <button className="secondary" type="button" disabled={editing !== null || paying !== null} onClick={() => setEditing(bill.id)}>Edit bill</button>
                <DeleteItem kind="bills" id={bill.id} name={bill.name} disabled={editing !== null || paying !== null} onDelete={() => {
                  setBills(previous => previous.filter(item => item.id !== bill.id))
                  onChange()
                  setNotice(`Deleted ${bill.name}.`)
                }} />
                {!bill.is_paid && <button type="button" disabled={editing !== null || paying !== null} onClick={() => setPaying(bill.id)}>{bill.recurring && billStatus(bill, currentDate) === 'paid' ? 'Pay next bill early' : 'Record payment'}</button>}
              </div>}
            </BillItem>
          ))}
        </div>
      </section>
    </aside>
  )
}







