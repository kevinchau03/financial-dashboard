import { useEffect, useRef, useState } from 'react'
import { amount, saveRecord, today } from '../api'
import type { Goal, Debt } from '../types'
import type { Account } from './AccountForm'
import type { PaychequeRecord } from '../paychequeTypes'
import Modal from './Modal'
import AppForm from './AppForm'

export default function PaychequePlan({ existing, initialAmount, onSave, onClose }: {
  existing?: PaychequeRecord; initialAmount: string; onSave: (pay: PaychequeRecord) => void; onClose: () => void
}) {
  const [value, setValue] = useState(initialAmount)
  const [date, setDate] = useState(today())
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
        const responses = await Promise.all(['/api/goals', '/api/debts', '/api/accounts'].map(url => fetch(url, { signal: controller.signal })))
        if (responses.some(response => !response.ok)) throw new Error('Unable to load goals, debts and accounts. Please retry.')
        const [goals, debts, accounts] = await Promise.all(responses.map(response => response.json())) as [Goal[], Debt[], Account[]]
        if (!controller.signal.aborted) setTargets([
          ...goals.map(goal => ({ kind: 'goal' as const, id: goal.id, name: goal.name, detail: `${amount(goal.current_amount)} saved of ${amount(goal.target_amount)}${goal.account_name ? ` - Deposit into ${goal.account_name}` : ''}`, max: '999999999999.99' })),
          ...debts.filter(debt => Number(debt.remaining_amount) > 0).map(debt => ({ kind: 'debt' as const, id: debt.id, name: debt.name, detail: `${amount(debt.remaining_amount)} remaining`, max: debt.remaining_amount })),
          ...accounts.map(account => ({ kind: 'account' as const, id: account.id, name: account.name, detail: `${account.account_type} · ${amount(account.balance)} recorded balance`, max: '999999999999.99' })),
        ])
      } catch (error) { if (!controller.signal.aborted) setLoadError(error instanceof Error ? error.message : 'Unable to load your targets.') }
      finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load(); return () => controller.abort()
  }, [retry])
  const total = Object.values(entries).reduce((sum, entry) => sum + Math.round(Number(entry || 0) * 100), 0)
  const available = Math.round(Number(existing?.remaining_amount ?? value) * 100)
  const left = available - total
  return <Modal title={existing ? 'Allocate more' : 'Plan your paycheque'} busy={saving} onClose={onClose}>
    <p className="plan-guidance">Give your paycheque a purpose. These are plans: record savings or payments after you make them. Leave some aside for bills and everyday spending. Accounts track where money is kept; goals track its purpose. Allocate each dollar once: a linked goal deposit updates its account and goal together. Do not also allocate that deposit to the account.</p>
    {loading && <p role="status">Loading your goals, debts and accounts…</p>}
    {loadError && <div role="alert"><p>{loadError}</p><button type="button" className="secondary" onClick={() => { setLoading(true); setLoadError(''); setRetry(previous => previous + 1) }}>Retry</button></div>}
    {!loading && !loadError && <AppForm onSubmit={async event => {
      event.preventDefault()
      if (left < 0) {
        setError('Your allocations exceed this paycheque. Reduce an amount to continue.')
        event.currentTarget.querySelector<HTMLInputElement>('[data-overallocated="true"]')?.focus()
        return
      }
      setSaving(true); setError('')
      const allocations = targets.flatMap(target => {
        const entry = entries[`${target.kind}-${target.id}`]
        return Number(entry) > 0 ? [{ kind: target.kind, target_id: target.id, amount: entry }] : []
      })
      try {
        onSave(await saveRecord<PaychequeRecord>(existing ? `/api/paycheques/${existing.id}/allocations` : '/api/paycheques', 'POST', {
          request_id: key.current, allocations, ...(!existing ? { amount: value, received_on: date } : {}),
        }))
      } catch (error) { setError(error instanceof Error ? error.message : 'Unable to save your plan. Retry with the same details.') }
      finally { setSaving(false) }
    }}>
      <fieldset disabled={saving}>
        {!existing && <div className="amount-fields">
          <label>Paycheque amount<input autoFocus name="paycheque_amount" type="number" required min="0.01" max="999999999999.99" step="0.01" value={value} onChange={event => { setError(''); setValue(event.target.value) }} /></label>
          <label>Received on<input name="received_on" type="date" required max={today()} value={date} onChange={event => setDate(event.target.value)} /></label>
        </div>}
        {existing && <p>Paycheque: {amount(existing.amount)} · {existing.received_on ?? 'Received date not recorded'}</p>}
        <div className="allocation-totals" aria-live="polite" aria-atomic="true">
          <div><small>Available</small><strong>{amount(String(available / 100))}</strong></div>
          <div><small>This plan</small><strong>{amount(String(total / 100))}</strong></div>
          <div><small>Left to allocate</small><strong className={left < 0 ? 'allocation-over' : ''}>{amount(String(left / 100))}</strong></div>
        </div>
        {!loading && !loadError && targets.length === 0 && <p>You have no goals, unpaid debts or accounts yet. Save this paycheque now and allocate it after adding one.</p>}
        {(['goal', 'debt', 'account'] as const).map(kind => targets.some(target => target.kind === kind) && <section key={kind} className="allocation-group">
          <h3>{kind === 'goal' ? 'Grow your goals' : kind === 'debt' ? 'Tackle your debts' : 'Build your accounts'}</h3>
          {targets.filter(target => target.kind === kind).map(target => {
            const id = `${kind}-${target.id}`
            return <label key={id} className="allocation-input"><span><strong>{target.name}</strong><small>{target.detail}</small></span>
              <input autoFocus={Boolean(existing) && targets[0] === target} aria-label={`Allocate to ${target.name}`} aria-invalid={left < 0 && Number(entries[id]) > 0} aria-describedby={left < 0 ? 'allocation-limit' : undefined} data-overallocated={left < 0 && Number(entries[id]) > 0} name={id} type="number" min="0" max={target.max} step="0.01" placeholder="0.00" value={entries[id] ?? ''} onChange={event => { setError(''); setEntries(previous => ({ ...previous, [id]: event.target.value })) }} />
            </label>
          })}
        </section>)}
        {left < 0 && <p id="allocation-limit" role="alert">Reduce your allocations by {amount(String(-left / 100))}.</p>}
        <button type="submit" disabled={loading || Boolean(loadError) || (Boolean(existing) && total === 0)}>{saving ? 'Saving…' : existing ? 'Save allocations' : 'Save paycheque & plan'}</button>
      </fieldset>
      {error && <p role="alert">{error}</p>}
    </AppForm>}
  </Modal>
}
