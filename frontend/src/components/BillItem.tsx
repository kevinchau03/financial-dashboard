import { useId, useState } from 'react'
import type { ReactNode } from 'react'
import type { Bill } from '../types'
import { amount } from '../api'
import { billStatus } from '../billStatus'

export default function BillItem({ bill, active, children, currentDate }: {
  bill: Bill; active: boolean; children: ReactNode; currentDate: string
}) {
  const [expanded, setExpanded] = useState(false)
  const id = useId()
  const open = active || expanded
  const status = billStatus(bill, currentDate)
  const daysUntilDue = bill.due_date
    ? Math.round((Date.parse(`${bill.due_date}T00:00:00Z`) - Date.parse(`${currentDate}T00:00:00Z`)) / 86400000)
    : null
  const timing = daysUntilDue === null ? '' : daysUntilDue === 0 ? 'today'
    : daysUntilDue === 1 ? 'tomorrow'
    : daysUntilDue > 0 ? `in ${daysUntilDue} days`
    : `${Math.abs(daysUntilDue)} ${daysUntilDue === -1 ? 'day' : 'days'} overdue`

  return <article className="compact-bill"
    onKeyDown={event => {
      if (event.key === 'Escape' && !active) {
        event.currentTarget.querySelector<HTMLButtonElement>('.bill-summary')?.focus()
        setExpanded(false)
        event.stopPropagation()
      }
    }}>
    <button type="button" className="bill-summary" aria-expanded={open} aria-controls={id}
      onClick={() => { if (!active) setExpanded(previous => !previous) }}>
      <span className="bill-summary-top"><span className="bill-name">{bill.name}</span><strong>{amount(bill.amount)}</strong></span>
      <span className="bill-summary-bottom">
        <span className={`status ${status}`}>{status === 'paid' ? 'Paid' : status === 'overdue' ? 'Overdue' : 'Unpaid'}</span>
        {!bill.recurring && <span className="bill-due">{bill.is_paid ? 'Settled' : bill.due_date ? `Due ${bill.due_date}` : 'No due date'}</span>}
        <span className="bill-expand" aria-hidden="true">{open ? '⌃' : '⌄'}</span>
      </span>
      {bill.recurring && <span className="bill-due">
        {!bill.due_date ? 'Next payment: not scheduled' : <>
          Next payment: {' '}
          <time dateTime={bill.due_date}>{bill.due_date}</time> · {timing}
        </>}
      </span>}
    </button>
    <div id={id} className="bill-preview" hidden={!open}>
      <p className="bill-meta">{bill.recurring ? 'Repeats monthly' : 'One-time bill'}{!bill.recurring && bill.is_paid && bill.due_date ? ` · Was due ${bill.due_date}` : ''}</p>
      {children}
    </div>
  </article>
}
