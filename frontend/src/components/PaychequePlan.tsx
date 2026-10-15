import { useEffect, useRef, useState } from 'react'
import { amount, saveRecord, today } from '../api'
import type { Goal, Debt, Bill } from '../types'
import type { Account } from './AccountForm'
import type { PaychequeRecord } from '../paychequeTypes'
import AppForm from './AppForm'

export default function PaychequePlan({ existing, previous, initialAmount, onSave, onClose }: {
  existing?: PaychequeRecord; previous?: PaychequeRecord; initialAmount: string; onSave: (pay: PaychequeRecord) => void; onClose: () => void
}) {
  const [value, setValue] = useState(initialAmount)
  const [date, setDate] = useState(today())
  const [nextPayday, setNextPayday] = useState('')
  const [billsReserved, setBillsReserved] = useState('')
  const [spendingReserved, setSpendingReserved] = useState('')
  const [bills, setBills] = useState<Bill[]>([])
  const [targets, setTargets] = useState<{ kind: 'goal' | 'debt' | 'account'; id: number; name: string; detail: string; max: string }[]>([])
  const [entries, setEntries] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [retry, setRetry] = useState(0)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const key = useRef(crypto.randomUUID())
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const responses = await Promise.all(['/api/goals', '/api/debts', '/api/accounts', '/api/bills'].map(url => fetch(url, { signal: controller.signal })))
        if (responses.some(response => !response.ok)) throw new Error('Unable to load goals, debts and accounts. Please retry.')
        const [goals, debts, accounts, loadedBills] = await Promise.all(responses.map(response => response.json())) as [Goal[], Debt[], Account[], Bill[]]
        if (!controller.signal.aborted) { setBills(loadedBills); setTargets([
          ...goals.map(goal => ({ kind: 'goal' as const, id: goal.id, name: goal.name, detail: `${amount(goal.current_amount)} saved of ${amount(goal.target_amount)}${goal.account_name ? ` - Deposit into ${goal.account_name}` : ''}`, max: '999999999999.99' })),
          ...debts.filter(debt => Number(debt.remaining_amount) > 0).map(debt => ({ kind: 'debt' as const, id: debt.id, name: debt.name, detail: `${amount(debt.remaining_amount)} remaining`, max: debt.remaining_amount })),
          ...accounts.map(account => ({ kind: 'account' as const, id: account.id, name: account.name, detail: `${account.account_type} · ${amount(account.balance)} recorded balance`, max: '999999999999.99' })),
        ]) }
      } catch (error) { if (!controller.signal.aborted) setLoadError(error instanceof Error ? error.message : 'Unable to load your targets.') }
      finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load(); return () => controller.abort()
  }, [retry])
  const total = Object.values(entries).reduce((sum, entry) => sum + Math.round(Number(entry || 0) * 100), 0)
  const available = Math.round(Number(existing?.remaining_amount ?? value) * 100)
  const reserved = existing ? 0 : Math.round(Number(billsReserved || 0) * 100) + Math.round(Number(spendingReserved || 0) * 100)
  const left = available - total - reserved
  const upcoming = bills.filter(bill => !bill.is_paid && bill.due_date && (!nextPayday || bill.due_date <= nextPayday)).sort((a, b) => (a.due_date ?? '').localeCompare(b.due_date ?? ''))
  const billTotal = upcoming.reduce((sum, bill) => sum + Math.round(Number(bill.amount) * 100), 0)
  return <div className="guided-plan">
    <p className="plan-guidance">Plan money you have received. Saving a plan does not move money or update your balances.</p>
    {loading && <p role="status">Loading your goals, debts and accounts…</p>}
    {loadError && <div role="alert"><p>{loadError}</p><button type="button" className="secondary" onClick={() => { setLoading(true); setLoadError(''); setRetry(previous => previous + 1) }}>Retry</button></div>}
    {!loading && !loadError && <AppForm onSubmit={async event => {
      event.preventDefault()
      if (left < 0) {
        setError('Your reserves and allocations exceed this paycheque. Reduce an amount to continue.');
        (event.currentTarget.querySelector<HTMLInputElement>('[data-overallocated="true"]') ?? event.currentTarget.querySelector<HTMLInputElement>('[name="bills_reserved"]'))?.focus()
        return
      }
      setSaving(true); setError('')
      const allocations = targets.flatMap(target => {
        const entry = entries[`${target.kind}-${target.id}`]
        return Number(entry) > 0 ? [{ kind: target.kind, target_id: target.id, amount: entry }] : []
      })
      try {
        onSave(await saveRecord<PaychequeRecord>(existing ? `/api/paycheques/${existing.id}/allocations` : '/api/paycheques', 'POST', {
          request_id: key.current, allocations, ...(!existing ? { amount: value, received_on: date, next_payday: nextPayday || null, bills_reserved: billsReserved || '0', spending_reserved: spendingReserved || '0' } : {}),
        }))
      } catch (error) { setError(error instanceof Error ? error.message : 'Unable to save your plan. Retry with the same details.') }
      finally { setSaving(false) }
    }}>
<p className="mobile-plan-total" role="status">Left to allocate <strong>{amount(String(left / 100))}</strong></p>
      <fieldset disabled={saving} className="planner-layout">
      <div className="planner-worksheet">
        {!existing && <section className="planner-section"><h2>1. Your paycheque</h2><div className="amount-fields">
          <label>Paycheque amount<input autoFocus name="paycheque_amount" type="number" required min="0.01" max="999999999999.99" step="0.01" value={value} onChange={event => { setError(''); setValue(event.target.value) }} /></label>
          <label>Received on<input name="received_on" type="date" required max={today()} value={date} onChange={event => setDate(event.target.value)} /></label>
          <label>Next payday (optional)<input name="next_payday" type="date" min={date} value={nextPayday} onChange={event => setNextPayday(event.target.value)} /></label>
        </div></section>}
        {!existing && <section className="planner-section"><h2>2. Keep everyday money available</h2><p>Set aside money for bills and daily life before choosing your savings. These reserves do not mark bills paid.</p>
          <details className="planner-bills"><summary>Upcoming and overdue unpaid bills ({upcoming.length})</summary>
            <div className="planner-bill-total"><span>Total for listed bills</span><strong>{amount(String(billTotal / 100))}</strong></div>
            {!nextPayday && <p>Choose your next payday to narrow this list.</p>}
            {upcoming.length ? <ul className="planner-bill-list">{upcoming.map(bill => <li key={bill.id}>
              <div><strong>{bill.name}</strong><span className={bill.due_date! < today() ? 'bill-date-overdue' : undefined}>{bill.due_date! < today() ? 'Overdue' : 'Due'} <time dateTime={bill.due_date!}>{bill.due_date}</time></span></div>
              <strong className="planner-bill-amount">{amount(bill.amount)}</strong>
            </li>)}</ul> : <p>No unpaid bills with due dates in this period.</p>}
            {upcoming.length > 0 && <button type="button" className="secondary" onClick={() => setBillsReserved((billTotal / 100).toFixed(2))}>Use bill total</button>}
          </details>
          <div className="amount-fields"><label>Reserve for bills<input name="bills_reserved" aria-invalid={left < 0 && Number(billsReserved) > 0} aria-describedby={left < 0 ? 'allocation-limit' : undefined} type="number" min="0" step="0.01" value={billsReserved} placeholder="0.00" onChange={event => setBillsReserved(event.target.value)} /></label>
          <label>Reserve for everyday spending<input name="spending_reserved" aria-invalid={left < 0 && Number(spendingReserved) > 0} aria-describedby={left < 0 ? 'allocation-limit' : undefined} type="number" min="0" step="0.01" value={spendingReserved} placeholder="0.00" onChange={event => setSpendingReserved(event.target.value)} /></label></div>
        </section>}
        <section className="planner-section"><h2>{existing ? 'Allocate the remainder' : '3. Choose what your money works toward'}</h2><p>Choose amounts for your goals and debts. Leaving money unallocated is okay.</p>
        {!existing && previous && <button type="button" className="secondary" onClick={() => {
          setBillsReserved(previous.bills_reserved); setSpendingReserved(previous.spending_reserved)
          const reused: Record<string, string> = {}
          for (const allocation of previous.allocations.filter(item => item.status !== 'cancelled')) {
            const targetId = allocation.kind === 'goal' ? allocation.goal_id : allocation.kind === 'debt' ? allocation.debt_id : allocation.account_id
            const target = targets.find(item => item.kind === allocation.kind && item.id === targetId)
            if (target) {
              const id = `${target.kind}-${target.id}`
              reused[id] = (Number(reused[id] || 0) + Number(allocation.amount)).toFixed(2)
            }
          }
          setEntries(reused)
        }}>Use previous paycheque amounts</button>}
        {!existing && previous && <p>Reuses reserves and active target amounts as an editable draft. Check them against this paycheque.</p>}
        {existing && <p>Paycheque: {amount(existing.amount)} · {existing.received_on ?? 'Received date not recorded'}</p>}
        {!loading && !loadError && targets.length === 0 && <p>You have no goals, unpaid debts or accounts yet. Save this paycheque now and allocate it after adding one.</p>}
        {(['goal', 'debt', 'account'] as const).map(kind => targets.some(target => target.kind === kind) && <details key={kind} className="allocation-group" open={kind !== 'account'}>
          <summary>{kind === 'goal' ? 'Grow your goals' : kind === 'debt' ? 'Tackle your debts' : 'Set aside in an account without a goal'}</summary>{kind === 'account' && <p>A linked goal already includes its account deposit. Allocate each dollar once.</p>}
          {targets.filter(target => target.kind === kind).map(target => {
            const id = `${kind}-${target.id}`
            return <div key={id} className="allocation-input"><label htmlFor={`allocation-${id}`}><span><strong>{target.name}</strong><small>{target.detail}</small></span></label>
              <input id={`allocation-${id}`} autoFocus={Boolean(existing) && targets[0] === target} aria-label={`Allocate to ${target.name}`} aria-invalid={left < 0 && Number(entries[id]) > 0} aria-describedby={left < 0 ? 'allocation-limit' : undefined} data-overallocated={left < 0 && Number(entries[id]) > 0} name={id} type="number" min="0" max={target.max} step="0.01" placeholder="0.00" value={entries[id] ?? ''} onChange={event => { setError(''); setEntries(previous => ({ ...previous, [id]: event.target.value })) }} />
              <button type="button" className="secondary" disabled={left <= 0} onClick={() => setEntries(previous => ({ ...previous, [id]: Math.min(Number(target.max), Number(previous[id] || 0) + left / 100).toFixed(2) }))}>Add remaining</button>
            </div>
          })}
        </details>)}
        </section></div><aside className="planner-summary"><h2>{existing ? 'Review allocations' : '4. Review your plan'}</h2><dl><div><dt>Received</dt><dd>{amount(existing?.amount ?? (value || '0'))}</dd></div><div><dt>Reserved</dt><dd>{amount(String((reserved + (existing ? Math.round(Number(existing.bills_reserved) * 100) + Math.round(Number(existing.spending_reserved) * 100) : 0)) / 100))}</dd></div><div><dt>{existing ? 'New allocations' : 'Allocated'}</dt><dd>{amount(String(total / 100))}</dd></div><div className={`planner-remainder${left < 0 ? ' allocation-over' : ''}`} aria-live="polite"><dt>Left to allocate</dt><dd>{amount(String(left / 100))}</dd></div></dl><p>Your plan stays separate from recorded savings and payments.</p>
        {left < 0 && <p id="allocation-limit" role="alert">Reduce your allocations by {amount(String(-left / 100))}.</p>}
        <button type="submit" disabled={loading || Boolean(loadError) || (Boolean(existing) && total === 0)}>{saving ? 'Saving…' : existing ? 'Save allocations' : 'Save plan'}</button>
        <button type="button" className="secondary" disabled={saving} onClick={onClose}>Cancel</button>
      </aside></fieldset>
      {error && <p role="alert">{error}</p>}
    </AppForm>}
  </div>
}
