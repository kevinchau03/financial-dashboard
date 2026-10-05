import { useRef, useState } from 'react'
import Modal from './Modal'

export default function DeleteItem({ kind, id, name, disabled, onDelete }: {
  kind: 'goals' | 'bills' | 'debts'; id: number; name: string; disabled?: boolean; onDelete: () => void
}) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef(false)
  const label = kind === 'goals' ? 'goal' : kind === 'bills' ? 'bill' : 'debt'

  async function remove() {
    if (pending.current) return
    pending.current = true
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`/api/${kind}/${id}`, { method: 'DELETE' })
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
    <button type="button" className="secondary" disabled={disabled} onClick={() => { setError(''); setOpen(true) }}>Delete {label}</button>
    {open && <Modal title={`Delete ${name}?`} busy={busy} onClose={() => setOpen(false)}>
      <p>This permanently removes this {label}{kind !== 'goals' ? ' and its payment history' : ''}. This cannot be undone.</p>
      <div className="actions">
        <button type="button" className="secondary" disabled={busy} onClick={() => setOpen(false)}>Cancel</button>
        <button type="button" disabled={busy} onClick={remove}>{busy ? 'Deleting…' : `Delete ${label}`}</button>
      </div>
      {error && <p role="alert">{error}</p>}
    </Modal>}
  </>
}
