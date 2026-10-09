import { useEffect, useState } from 'react'
import { amount } from '../api'
import type { PaychequeRecord } from '../paychequeTypes'
import AppForm from './AppForm'
import Notice from './Notice'
import useNotice from '../hooks/useNotice'
import PaychequePlan from './PaychequePlan'
import PaychequeAllocations from './PaychequeAllocations'
import PaychequeHistory from './PaychequeHistory'
import DeleteItem from './DeleteItem'
import '../styles/paycheques.css'

export default function Paycheque({ onCompleted }: { onCompleted: () => void }) {
  const [saved, setSaved] = useState<PaychequeRecord | null>(null)
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const [modal, setModal] = useState<'new' | 'more' | 'history' | null>(null)
  const [notice, setNotice] = useNotice()
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await fetch('/api/paycheques/latest', { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load your latest paycheque.')
        const data: PaychequeRecord | null = await response.json()
        if (!controller.signal.aborted) setSaved(data)
      } catch (error) { if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load paycheque.') }
      finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load(); return () => controller.abort()
  }, [retry])
  return <section className="paycheque-card paycheque-planner" aria-label="Paycheque planning">
    <AppForm onSubmit={event => { event.preventDefault(); setModal('new') }}>
      <fieldset disabled={loading || Boolean(error)}>
        <label htmlFor="paycheque-amount">Just got your paycheque? Put in how much</label>
        <div className="contribution-controls"><input id="paycheque-amount" name="amount" type="number" required min="0.01" max="999999999999.99" step="0.01" value={value} onChange={event => setValue(event.target.value)} placeholder="0.00" /><button type="submit">Allocate paycheque</button></div>
      </fieldset>
    </AppForm>
    {loading && <p role="status">Loading paycheque…</p>}
    {error && <div role="alert"><p>{error}</p><button type="button" className="secondary" onClick={() => { setLoading(true); setError(''); setRetry(previous => previous + 1) }}>Retry</button></div>}
    {!loading && !error && !saved && <p className="plan-guidance">Start with your take-home pay, then choose what goes toward goals, debts and accounts. You can leave money unallocated.</p>}
    {saved && <div className="paycheque-overview">
      <div className="list-heading"><div><h2>Paycheque #{saved.id}</h2><p>{saved.received_on ?? 'Received date not recorded'}</p></div><button type="button" className="secondary" onClick={() => setModal('history')}>Paycheque history</button></div>
      <div className="allocation-totals"><div><small>Received</small><strong>{amount(saved.amount)}</strong></div><div><small>Allocated</small><strong>{amount(saved.allocated_amount)}</strong></div><div><small>Left to allocate</small><strong>{amount(saved.remaining_amount)}</strong></div></div>
      <div className="actions"><button type="button" disabled={Number(saved.remaining_amount) <= 0} onClick={() => setModal('more')}>Allocate more</button><small>Allocations stay planned until you record them as saved, paid or deposited.</small><DeleteItem kind="paycheques" id={saved.id} name={`Paycheque #${saved.id}`} onDelete={() => { setSaved(null); setLoading(true); setError(''); setRetry(previous => previous + 1); setNotice('Paycheque deleted. Recorded balances and payments were kept.') }} /></div>
      {saved.allocations.length > 0 && <details key={saved.id} open={saved.allocations.some(item => item.status === 'planned')}><summary>Your allocations ({saved.allocations.filter(item => item.status === 'planned').length} planned)</summary><PaychequeAllocations pay={saved} onSave={setSaved} onCompleted={() => { onCompleted(); setNotice('Recorded. Your progress is up to date.') }} /></details>}
    </div>}
    <Notice message={notice} />
    {(modal === 'new' || (modal === 'more' && saved)) && <PaychequePlan existing={modal === 'more' ? saved! : undefined} initialAmount={value} onClose={() => setModal(null)} onSave={pay => { setSaved(pay); if (modal === 'new') setValue(''); setModal(null); setNotice('Paycheque plan saved.') }} />}
    {modal === 'history' && <PaychequeHistory onClose={() => setModal(null)} onSelect={pay => { setSaved(pay); setModal(null) }} />}
  </section>
}
