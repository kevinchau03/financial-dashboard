import { useEffect, useState } from 'react'
import type { PaychequeRecord } from '../paychequeTypes'
import { amount } from '../api'
import Modal from './Modal'

export default function PaychequeHistory({ onSelect, onClose }: { onSelect: (pay: PaychequeRecord) => void; onClose: () => void }) {
  const [items, setItems] = useState<PaychequeRecord[]>([])
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await fetch(`/api/paycheques?offset=${offset}&limit=21`, { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load paycheques.')
        const data: PaychequeRecord[] = await response.json()
        if (!controller.signal.aborted) setItems(data)
      } catch (error) { if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load history.') }
      finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load(); return () => controller.abort()
  }, [offset, retry])
  return <Modal title="Your paycheques" onClose={onClose}>
    {loading ? <p role="status">Loading paycheques…</p> : error ? <div role="alert"><p>{error}</p><button type="button" onClick={() => { setLoading(true); setError(''); setRetry(value => value + 1) }}>Retry</button></div> : <>
      {items.length === 0 && <p>No paycheques saved yet.</p>}
      <ul className="paycheque-history">{items.slice(0, 20).map(pay => <li key={pay.id}><button type="button" className="secondary" onClick={() => onSelect(pay)}>
        <strong>{amount(pay.amount)}</strong><span>{pay.received_on ?? 'Received date not recorded'} · #{pay.id}</span><small>{amount(pay.remaining_amount)} left to allocate</small>
      </button></li>)}</ul>
      <div className="actions"><button className="secondary" disabled={offset === 0} onClick={() => { setLoading(true); setOffset(value => Math.max(0, value - 20)) }}>Previous</button><button className="secondary" disabled={items.length <= 20} onClick={() => { setLoading(true); setOffset(value => value + 20) }}>Next</button></div>
    </>}
  </Modal>
}
