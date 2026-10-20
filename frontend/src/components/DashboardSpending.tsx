import useDashboardResource from '../hooks/useDashboardResource'
import DashboardPanel from './DashboardPanel'
import StatCard from './StatCard'
import type { SavedStatement } from '../statementTypes'
import { statementDate } from '../statementTypes'
import { amount } from '../api'

type Summary = { stats: { total_income: string; total_spent: string; start_date: string | null; end_date: string | null } }

function StatementSummary({ statement }: { statement: SavedStatement }) {
  const resource = useDashboardResource<Summary>(`/api/statements/${statement.statement_id}/summary`)
  return <>
    <p className="overview-caption">Latest statement: <strong>{statement.filename}</strong></p>
    <p className="overview-caption">{statement.start_date && statement.end_date ? `${statementDate(statement.start_date)} – ${statementDate(statement.end_date)}` : 'No transaction dates recorded'}</p>
    <div className="overview-spending-stats">
      <StatCard tone="leaf" title="Money in" value={amount(resource.data?.stats.total_income ?? '0')} loading={resource.loading} error={resource.error} onRetry={resource.retry} />
      <StatCard tone="rose" title="Money out" value={amount(resource.data?.stats.total_spent ?? '0')} loading={resource.loading} error={resource.error} onRetry={resource.retry} />
    </div>
    <p className="overview-caption">This statement only; includes transfers and repayments.</p>
    <a className="button-link wrapped-dashboard-action" href={`#/budget-wrapped?statement=${statement.statement_id}`}>View Your Budget Wrapped</a>
  </>
}

export default function DashboardSpending() {
  const resource = useDashboardResource<{ items: SavedStatement[] }>('/api/statements?limit=1')
  const latest = resource.data?.items[0]
  return <DashboardPanel tone="sky" title="Latest statement" href="#/budget-wrapped" action="View all" loading={resource.loading} error={resource.error} onRetry={resource.retry}>
    {latest ? <StatementSummary statement={latest} /> : <div className="overview-empty"><h3>No statements yet</h3><p>Upload a TD CSV to see money in and out.</p><a href="#/budget-wrapped">Upload your first statement →</a></div>}
  </DashboardPanel>
}

