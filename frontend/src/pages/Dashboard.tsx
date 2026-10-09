import useDashboardResource from '../hooks/useDashboardResource'
import DashboardPanel from '../components/DashboardPanel'
import DashboardSpending from '../components/DashboardSpending'
import StatCard from '../components/StatCard'
import type { Account } from '../components/AccountForm'
import type { Goal, Debt, Bill } from '../types'
import { amount, today } from '../api'
import { statementDate } from '../statementTypes'
import { sumAmounts, upcomingBills } from '../dashboardSummary'
import '../styles/budget.css'
import '../styles/overview.css'

export default function Dashboard() {
  const accounts = useDashboardResource<Account[]>('/api/accounts')
  const goals = useDashboardResource<Goal[]>('/api/goals')
  const debts = useDashboardResource<Debt[]>('/api/debts')
  const bills = useDashboardResource<Bill[]>('/api/bills')
  const reminders = upcomingBills(bills.data ?? [])
  const overdue = reminders.filter(bill => bill.due_date && bill.due_date < today())
  return <div className="overview-page">
    <div className="page-intro overview-intro"><div><span className="budget-eyebrow">Your money, at a glance</span><h1>Your dashboard</h1><p>See where you stand, then give your next paycheque a purpose.</p></div><a className="button-link" href="#/budget">Plan your budget</a></div>
    <div className="overview-metrics">
      <StatCard tone="sky" title="Account balances" value={amount(sumAmounts((accounts.data ?? []).map(account => account.balance)))} description="Manually recorded across your accounts." loading={accounts.loading} error={accounts.error} onRetry={accounts.retry} />
      <StatCard tone="leaf" title="Total saved" value={amount(sumAmounts((goals.data ?? []).map(goal => goal.current_amount)))} description="Recorded savings. Planned allocations are excluded." loading={goals.loading} error={goals.error} onRetry={goals.retry} />
      <StatCard tone="rose" title="Total debt" value={amount(sumAmounts((debts.data ?? []).map(debt => debt.remaining_amount)))} description="The outstanding balance of tracked debts." loading={debts.loading} error={debts.error} onRetry={debts.retry} />
      <StatCard tone="sun" title="Total bills" value={amount(sumAmounts((bills.data ?? []).map(bill => bill.amount)))} description="All recorded bill amounts, including paid bills. Not a monthly projection." loading={bills.loading} error={bills.error} onRetry={bills.retry} />
    </div>
    <p className="overview-caption overview-balance-note">Account balances and goal savings are tracked separately and may represent the same money. They are not added together.</p>
    <div className="overview-grid">
      <div className="overview-primary">
        <DashboardPanel tone="sky" title="Your accounts" href="#/accounts" action="Manage accounts" loading={accounts.loading} error={accounts.error} onRetry={accounts.retry}>
          {accounts.data?.length ? <ul className="overview-list">{accounts.data.slice(0, 4).map(account => <li key={account.id}><div><strong>{account.name}</strong><small>{account.account_type}</small></div><strong>{amount(account.balance)}</strong></li>)}</ul> : <div className="overview-empty"><h3>Start with where your money lives</h3><p>Add a chequing, savings, or investment account and its current balance.</p><a href="#/accounts">Add your first account →</a></div>}
          {(accounts.data?.length ?? 0) > 4 && <p className="overview-caption">Showing 4 of {accounts.data!.length} accounts.</p>}
        </DashboardPanel>
        <div className="overview-progress-grid">
          <DashboardPanel tone="leaf" title="Goal progress" href="#/budget" action="Manage goals" loading={goals.loading} error={goals.error} onRetry={goals.retry}>
            {goals.data?.length ? <ul className="overview-progress-list">{goals.data.slice(0, 4).map(goal => <li key={goal.id}><strong>{goal.name}</strong><p>{amount(goal.current_amount)} saved of {amount(goal.target_amount)}</p><progress value={Number(goal.current_amount)} max={Number(goal.target_amount)} aria-label={`${goal.name} savings progress`} /><small>{Number(goal.current_amount) >= Number(goal.target_amount) ? 'Goal reached' : `${Math.floor(Number(goal.current_amount) / Number(goal.target_amount) * 100)}% saved`}</small></li>)}</ul> : <div className="overview-empty"><h3>Give your savings a purpose</h3><p>Choose a target and track your progress in Budget.</p><a href="#/budget">Create a goal →</a></div>}
            {(goals.data?.length ?? 0) > 4 && <p className="overview-caption">Showing 4 of {goals.data!.length} goals.</p>}
          </DashboardPanel>
          <DashboardPanel tone="rose" title="Debt progress" href="#/budget" action="Manage debts" loading={debts.loading} error={debts.error} onRetry={debts.retry}>
            {debts.data?.length ? <ul className="overview-progress-list">{debts.data.slice(0, 4).map(debt => <li key={debt.id}><strong>{debt.name}</strong><p>{amount(debt.remaining_amount)} remaining of {amount(debt.amount)}</p><progress value={Number(debt.current_amount)} max={Number(debt.amount)} aria-label={`${debt.name} repayment progress`} /><small>{Number(debt.remaining_amount) === 0 ? 'Paid off' : `${Math.floor(Number(debt.current_amount) / Number(debt.amount) * 100)}% repaid`}</small></li>)}</ul> : <div className="overview-empty"><h3>A clearer path to debt-free</h3><p>Track a debt and the payments you have made toward it.</p><a href="#/budget">Add a debt →</a></div>}
            {(debts.data?.length ?? 0) > 4 && <p className="overview-caption">Showing 4 of {debts.data!.length} debts.</p>}
          </DashboardPanel>
        </div>
      </div>
      <div className="overview-secondary">
        <DashboardPanel tone="sun" title="Bill reminders" href="#/budget" action="Manage bills" loading={bills.loading} error={bills.error} onRetry={bills.retry}>
          {overdue.length > 0 && <p className="overview-alert">{overdue.length} {overdue.length === 1 ? 'bill is' : 'bills are'} overdue.</p>}
          {reminders.length ? <ul className="overview-list overview-bills">{reminders.slice(0, 4).map(bill => <li key={bill.id}><div><strong>{bill.name}</strong><small>{bill.due_date ? `${bill.due_date < today() ? 'Overdue' : bill.due_date === today() ? 'Due today' : 'Next payment'} · ${statementDate(bill.due_date)}` : 'No due date set'}{bill.recurring ? ' · Monthly' : ''}</small></div><strong>{amount(bill.amount)}</strong></li>)}</ul> : <div className="overview-empty"><h3>{bills.data?.length ? 'All caught up' : 'Keep upcoming payments in view'}</h3><p>{bills.data?.length ? 'No unpaid or recurring bills to remind you about.' : 'Add your bills in Budget to see reminders here.'}</p><a href="#/budget">Manage your bills →</a></div>}
          {reminders.length > 4 && <p className="overview-caption">Showing the next 4 of {reminders.length} bill reminders.</p>}
        </DashboardPanel>
        <DashboardSpending />
      </div>
    </div>
  </div>
}

