import { useRef, useState } from 'react'
import type { Payment } from '../types'
import { amount } from '../api'
import { paymentDate } from '../activity'
import Modal from './Modal'

export default function UndoPayment({ payment, onUndo }: { payment: Payment; onUndo: () => void }) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef(false)

  async function undo() {
    if (pending.current) return
    pending.current = true
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`/api/payments/${payment.id}`, {
        method: 'DELETE', signal: AbortSignal.timeout(15000),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(typeof body?.detail === 'string' ? body.detail : 'Unable to undo this payment. Please try again.')
      }
      setOpen(false)
      onUndo()
    } catch (error) {
      setError(error instanceof Error && error.name !== 'TimeoutError' && error.name !== 'TypeError'
        ? error.message : 'Unable to confirm whether the payment was undone. Check your connection and retry; retrying will not reverse it twice.')
    } finally {
      pending.current = false
      setBusy(false)
    }
  }

  return <>
    <button type="button" className="secondary activity-undo" disabled={!!payment.undo_unavailable_reason}
      aria-label={`Undo ${amount(payment.amount)} payment to ${payment.target_name}`}
      title={payment.undo_unavailable_reason ?? 'Undo payment'} onClick={() => { setError(''); setOpen(true) }}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M9 4 4 9l5 5M4 9h9a7 7 0 0 1 0 14" transform="translate(0 -2)" /></svg>
      <span>Undo</span>
    </button>
    {payment.undo_unavailable_reason && <small className="activity-undo-reason">{payment.undo_unavailable_reason}</small>}
    {open && <Modal title="Undo payment?" busy={busy} onClose={() => setOpen(false)}>
      <p>Undo the <strong>{amount(payment.amount)}</strong> recorded for <strong>{payment.target_name}</strong> on {paymentDate(payment.paid_on)}?</p>
      <p>{payment.kind === 'bill'
        ? 'This restores the bill’s previous payment status and due date. Only the most recently recorded payment can be undone, and later schedule edits must remain intact.'
        : payment.kind === 'debt' ? 'This reduces the amount recorded as paid and increases the debt remaining.'
          : 'This reduces recorded goal savings. Any account deposit made by this contribution is reversed in its original account; money assigned from an existing balance stays in the account.'}</p>
      {payment.source === 'paycheque' && <p>If its paycheque allocation still exists, it will be cancelled and its money made available to allocate again.</p>}
      <p>The payment will leave Activity history. No money is transferred.</p>
      <div className="actions">
        <button type="button" className="secondary" disabled={busy} onClick={() => setOpen(false)}>Cancel</button>
        <button type="button" className="danger activity-undo-confirm" disabled={busy} onClick={undo}>{busy ? 'Undoing…' : 'Undo payment'}</button>
      </div>
      {error && <p role="alert">{error}</p>}
    </Modal>}
  </>
}
