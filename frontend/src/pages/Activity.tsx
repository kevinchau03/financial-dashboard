import { useEffect, useRef } from 'react'
import { amount } from '../api'
import { activityFilters, activityHref, paymentDate } from '../activity'
import type { ActivityPage } from '../activity'
import useHash from '../hooks/useHash'
import useDashboardResource from '../hooks/useDashboardResource'
import '../styles/activity.css'

const filters = [ ['all', 'All activity'], ['debt', 'Debts'], ['goal', 'Goals'], ['bill', 'Bills'] ] as const
const kindLabels = { bill: 'Bill payment', debt: 'Debt payment', goal: 'Goal contribution' }
const sourceLabels = { manual: 'Direct entry', paycheque: 'Paycheque allocation', legacy: 'Previous payment history' }

export default function Activity() {
  const { kind, page } = activityFilters(useHash())
  const params = new URLSearchParams({ page: String(page), page_size: '20' })
  if (kind !== 'all') params.set('kind', kind)
  const { data, loading, error, retry } = useDashboardResource<ActivityPage>(
    `/api/payments?${params}`, 'Unable to load activity. Check your connection and retry.',
  )
  const heading = useRef<HTMLHeadingElement>(null)
  const previousPage = useRef(page)
  useEffect(() => {
    if (!loading && previousPage.current !== page) heading.current?.focus({ preventScroll: true })
    if (!loading) previousPage.current = page
  }, [loading, page])
  useEffect(() => {
    if (data && data.page !== page) window.location.replace(activityHref(kind, data.page))
  }, [data, kind, page])

  return <div className="activity-page">
    <div className="page-intro list-heading">
      <div><h1>Activity history</h1><p>Your recorded payments and progress, in one place.</p></div>
      <a className="activity-record-link" href="#/budget">Record a payment <span aria-hidden="true">↗</span></a>
    </div>
    <p className="activity-explanation">Debt payments, goal contributions and paid bills. Only completed records appear here; planned allocations stay in your paycheque planner.</p>
    <nav className="activity-filters" aria-label="Filter activity">
      {filters.map(([value, label]) => <a key={value} href={activityHref(value)} aria-current={kind === value ? 'true' : undefined}>{label}</a>)}
    </nav>
    <div className="activity-ledger-heading">
      <h2 ref={heading} tabIndex={-1}>Recorded activity</h2>
      <p>Newest payment date first · CAD</p>
    </div>
    <div className="activity-results" aria-busy={loading}>
      {loading && <div className="activity-state" role="status">Loading activity…</div>}
      {error && <div className="activity-state"><p role="alert">{error}</p><button type="button" onClick={retry}>Retry</button></div>}
      {data && data.total === 0 && <div className="activity-state">
        <h3>{kind === 'all' ? 'No activity recorded yet' : `No ${kind === 'goal' ? 'goal contributions' : `${kind} payments`} recorded`}</h3>
        <p>Record a payment in Budget or complete a paycheque allocation to see it here.</p>
        <a href="#/budget">Open your budget</a>
        {kind !== 'all' && <a href={activityHref('all')}>View all activity</a>}
      </div>}
      {data && data.items.length > 0 && <div className="activity-table-scroll" tabIndex={0} role="region" aria-label="Payment history; scroll horizontally on small screens">
        <table className="activity-table">
          <caption className="sr-only">Completed payments and contributions, newest payment date first. Amounts in Canadian dollars.</caption>
          <thead><tr><th scope="col">Payment date</th><th scope="col">Activity</th><th scope="col">Recorded through</th><th scope="col" className="activity-amount">Amount</th></tr></thead>
          <tbody>{data.items.map(payment => <tr key={payment.id}>
            <td><time dateTime={payment.paid_on}>{paymentDate(payment.paid_on)}</time></td>
            <td><span className={`activity-kind activity-kind-${payment.kind}`}>{kindLabels[payment.kind]}</span><strong className="activity-target">{payment.target_name}</strong>{payment.target_id === null && <small>Item deleted · history retained</small>}</td>
            <td><span>{sourceLabels[payment.source]}</span>{payment.recorded_at && <small>Recorded <time dateTime={payment.recorded_at}>{new Date(payment.recorded_at).toLocaleString(undefined, { timeZoneName: 'short' })}</time></small>}</td>
            <td className="activity-amount">{amount(payment.amount)}</td>
          </tr>)}</tbody>
        </table>
      </div>}
    </div>
    {data && <nav className="activity-pagination" aria-label="Activity pages">
      <p role="status">{data.total === 0 ? '0 records' : `${(data.page - 1) * data.page_size + 1}–${Math.min(data.page * data.page_size, data.total)} of ${data.total} records`}</p>
      <div><button type="button" className="secondary" disabled={data.page === 1} onClick={() => { window.location.hash = activityHref(kind, data.page - 1) }}>Previous</button><span>Page {data.page} of {data.pages}</span><button type="button" className="secondary" disabled={data.page === data.pages} onClick={() => { window.location.hash = activityHref(kind, data.page + 1) }}>Next</button></div>
    </nav>}
    <p className="activity-footnote">Records describe money you have tracked here. Opening balances and older goal additions without a saved payment record are not included.</p>
  </div>
}
