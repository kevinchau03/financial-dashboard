import { useState } from 'react'
import type { Allocation, PaychequeRecord } from '../paychequeTypes'
import { amount, saveRecord, today } from '../api'
import Modal from './Modal'
import AppForm from './AppForm'

export default function PaychequeAllocations({ pay, onSave, onCompleted }: {
  pay: PaychequeRecord; onSave: (pay: PaychequeRecord) => void; onCompleted: () => void
}) {
  const [recording, setRecording] = useState<Allocation | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  return <>
    <ul className="allocation-list">{pay.allocations.map(item => <li key={item.id}>
      <div><strong>{item.name}</strong><small>{item.kind === 'goal' ? 'Savings goal' : item.kind === 'account' ? 'Account' : 'Debt'} · {item.status === 'completed' ? `Recorded ${item.completed_on}` : item.status === 'cancelled' ? 'Cancelled · amount released' : 'Planned'}</small></div>
      <strong>{amount(item.amount)}</strong>
      {item.status === 'planned' && <div className="actions">
        <button type="button" disabled={busy} onClick={() => { setError(''); setRecording(item) }}>Record as {item.kind === 'debt' ? 'paid' : item.kind === 'account' ? 'deposited' : 'saved'}</button>
        <button type="button" className="secondary" disabled={busy} onClick={async () => {
          setBusy(true); setError('')
          try { onSave(await saveRecord<PaychequeRecord>(`/api/paycheques/${pay.id}/allocations/${item.id}/cancel`, 'POST', {})) }
          catch (error) { setError(error instanceof Error ? error.message : 'Unable to cancel allocation.') }
          finally { setBusy(false) }
        }}>Cancel allocation</button>
      </div>}
    </li>)}</ul>
    {error && !recording && <p role="alert">{error}</p>}
    {recording && <Modal title={`Record ${recording.kind === 'debt' ? 'payment' : recording.kind === 'account' ? 'deposit' : 'savings'}`} busy={busy} onClose={() => setRecording(null)}>
      <p>Record {amount(recording.amount)} toward <strong>{recording.name}</strong> only after you have {recording.kind === 'debt' ? 'paid' : recording.kind === 'account' ? 'deposited' : 'saved'} it. No money is sent.</p>
      <p className="plan-guidance">Already included this in the account balance or recorded it using a quick update? Close this window and cancel the plan to avoid counting it twice.</p>
      <AppForm onSubmit={async event => {
        event.preventDefault(); setBusy(true); setError('')
        const data = new FormData(event.currentTarget)
        try {
          const saved = await saveRecord<PaychequeRecord>(`/api/paycheques/${pay.id}/allocations/${recording.id}/complete`, 'POST', { completed_on: data.get('completed_on') })
          onSave(saved); onCompleted(); setRecording(null)
        } catch (error) { setError(error instanceof Error ? error.message : 'Unable to record allocation.') }
        finally { setBusy(false) }
      }}>
        <fieldset disabled={busy}>
          <label>{recording.kind === 'debt' ? 'Paid on' : recording.kind === 'account' ? 'Deposited on' : 'Saved on'}<input name="completed_on" type="date" required min={pay.received_on ?? undefined} max={today()} defaultValue={today()} /></label>
          <button type="submit">{busy ? 'Recording…' : recording.kind === 'debt' ? 'Confirm payment' : recording.kind === 'account' ? 'Confirm deposit' : 'Confirm savings'}</button>
        </fieldset>
        {error && <p role="alert">{error}</p>}
      </AppForm>
    </Modal>}
  </>
}
