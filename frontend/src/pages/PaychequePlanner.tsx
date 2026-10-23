import { apiFetch } from '../auth'
import { useEffect, useState } from 'react'
import { amount } from '../api'
import type { PaychequeRecord } from '../paychequeTypes'
import PaychequePlan from '../components/PaychequePlan'
import PaychequeAllocations from '../components/PaychequeAllocations'
import PaychequeHistory from '../components/PaychequeHistory'
import DeleteItem from '../components/DeleteItem'
import '../styles/budget.css'
import '../styles/paycheques.css'

export default function PaychequePlanner() {
  const [saved, setSaved] = useState<PaychequeRecord | null>(null)
  const [mode, setMode] = useState<'view' | 'new' | 'more'>('view')
  const [history, setHistory] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    apiFetch('/api/paycheques/latest', { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('Unable to load your latest paycheque.')
      const pay: PaychequeRecord | null = await response.json()
      if (!controller.signal.aborted) { setSaved(pay); setMode(pay ? 'view' : 'new') }
    }).catch(error => { if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load paycheque.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [retry])
  return <div className="budget-page paycheque-page">
    <a href="#/budget">Back to Budget</a>
    <div className="budget-header"><div className="page-intro"><span className="budget-eyebrow">A purpose for your pay</span><h1>Paycheque planner</h1><p>Cover everyday life, then make room for what matters next.</p></div>
      <button type="button" className="secondary" disabled={mode !== 'view'} title={mode !== 'view' ? 'Save or cancel your draft to open history' : undefined} onClick={() => setHistory(true)}>History</button></div>
    {loading ? <p role="status">Loading your paycheque...</p> : error ? <div role="alert"><p>{error}</p><button onClick={() => { setLoading(true); setError(''); setRetry(value => value + 1) }}>Retry</button></div> : mode === 'new' || mode === 'more' ?
      <PaychequePlan previous={saved ?? undefined} key={mode + (saved?.id ?? '')} existing={mode === 'more' && saved ? saved : undefined} initialAmount="" onClose={() => { if (saved) setMode('view'); else window.location.hash = '#/budget' }} onSave={pay => { setSaved(pay); setMode('view'); requestAnimationFrame(() => document.getElementById('saved-plan-heading')?.focus()) }} /> : saved &&
      <section className="planner-section"><h2 id="saved-plan-heading" tabIndex={-1}>Your saved plan</h2><p>{saved.received_on ?? 'Received date not recorded'} - {amount(saved.amount)} received</p>
        <div className="allocation-totals"><div><small>Reserved for bills</small><strong>{amount(saved.bills_reserved)}</strong></div><div><small>Everyday spending</small><strong>{amount(saved.spending_reserved)}</strong></div><div><small>Left to allocate</small><strong>{amount(saved.remaining_amount)}</strong></div></div>
        <p>Allocations are planned until you record them. No money is moved by this app.</p>
        <PaychequeAllocations pay={saved} onSave={setSaved} onCompleted={() => {}} />
        {!saved.allocations.length && <p>No goals or debts allocated yet. Your reserves are saved.</p>}
        <div className="actions"><button disabled={Number(saved.remaining_amount) <= 0} onClick={() => setMode('more')}>Allocate more</button><button className="secondary" onClick={() => setMode('new')}>Plan another paycheque</button><DeleteItem kind="paycheques" id={saved.id} name={`Paycheque #${saved.id}`} onDelete={() => { setLoading(true); setError(''); setRetry(value => value + 1) }} /></div>
      </section>}
    {history && <PaychequeHistory onClose={() => setHistory(false)} onSelect={pay => { setSaved(pay); setMode('view'); setHistory(false) }} />}
  </div>
}
