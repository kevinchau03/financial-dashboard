import { useRef, useState } from 'react'
import Modal from './Modal'

export default function DeleteItem({ kind, id, name, disabled, onDelete, resolve = false }: {
  kind: 'goals' | 'bills' | 'debts' | 'paycheques'; id: number; name: string; disabled?: boolean; onDelete: () => void; resolve?: boolean
}) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef(false)
  const label = kind === 'goals' ? 'goal' : kind === 'bills' ? 'bill' : kind === 'paycheques' ? 'paycheque' : 'debt'

  const resolving = kind === 'debts' && resolve
  const action = resolving ? 'Resolve debt' : `Delete ${label}`

  async function remove() {
    if (pending.current) return
    pending.current = true
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`/api/${kind}/${id}${resolving ? '?resolve=true' : ''}`, { method: 'DELETE' })
      // Already removed records can safely be removed from the local list too.
      if (!response.ok && response.status !== 404) {
        const body = await response.json().catch(() => null)
        throw new Error(typeof body?.detail === 'string' ? body.detail : 'Unable to delete. Please try again.')
      }
      setOpen(false)
      onDelete()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to delete.')
    } finally {
      pending.current = false
      setBusy(false)
    }
  }

  return <>
    <button type="button" className="secondary" disabled={disabled} onClick={() => { setError(''); setOpen(true) }}>{action}</button>
    {open && <Modal title={`${resolving ? 'Resolve' : 'Delete'} ${name}?`} busy={busy} onClose={() => setOpen(false)}>
      {resolving ? <p>This debt is paid off. Resolving it permanently deletes the debt and its payment history. This cannot be undone.</p> : kind === 'paycheques' ? <p>This permanently removes this paycheque and its allocation history, including unfinished plans. Recorded goal savings, account balances and debt payments stay unchanged. This cannot be undone.</p> : <p>This permanently removes this {label}{kind !== 'goals' ? ' and its payment history' : ''}. This cannot be undone.</p>}
      <div className="actions">
        <button type="button" className="secondary" disabled={busy} onClick={() => setOpen(false)}>Cancel</button>
        <button type="button" disabled={busy} onClick={remove}>{busy ? 'Deleting…' : action}</button>
      </div>
      {error && <p role="alert">{error}</p>}
    </Modal>}
  </>
}
