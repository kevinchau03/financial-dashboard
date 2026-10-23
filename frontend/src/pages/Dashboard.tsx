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
  const goalPreview = [...(goals.data ?? [])].sort((a, b) => Number(Number(a.current_amount) >= Number(a.target_amount)) - Number(Number(b.current_amount) >= Number(b.target_amount)))
  const completedGoals = (goals.data ?? []).filter(goal => Number(goal.current_amount) >= Number(goal.target_amount)).length
  const nextBill = reminders[0]
  return <div className="overview-page">
    <div className="page-intro overview-intro"><div><h1>Your Dashboard</h1></div><a className="button-link" href="#/budget/paycheques">Plan a paycheque</a></div>
    <div className="overview-metrics">
      <StatCard tone="sky" title="Account balances" value={amount(sumAmounts((accounts.data ?? []).map(account => account.balance)))} description="Manually recorded" loading={accounts.loading} error={accounts.error} onRetry={accounts.retry} />
      <StatCard tone="leaf" title="Total saved" value={amount(sumAmounts((goals.data ?? []).map(goal => goal.current_amount)))} description="Saved toward goals" loading={goals.loading} error={goals.error} onRetry={goals.retry} />
      <StatCard tone="rose" title="Total debt" value={amount(sumAmounts((debts.data ?? []).map(debt => debt.remaining_amount)))} description="Remaining balance" loading={debts.loading} error={debts.error} onRetry={debts.retry} />
    </div>
    {!bills.loading && !bills.error && nextBill && <div className={`overview-next-payment${overdue.length ? ' has-overdue' : ''}`}>
      <span>{overdue.length ? `${overdue.length} ${overdue.length === 1 ? 'bill needs' : 'bills need'} attention` : 'Next payment'}</span>
      <strong>{nextBill.name}</strong><span>{amount(nextBill.amount)}</span>
      <span>{nextBill.due_date ? `${nextBill.due_date < today() ? 'Overdue since' : 'Due'} ${statementDate(nextBill.due_date)}` : 'Set a due date'}</span>
      <a href="#/budget">Review bills</a>
    </div>}
    <div className="overview-grid">
        <div className="overview-progress-grid">
          <DashboardPanel tone="leaf" title="Goal progress" href="#/budget" action="View goals" loading={goals.loading} error={goals.error} onRetry={goals.retry}>
            {goals.data?.length ? <ul className="overview-progress-list">{goalPreview.slice(0, 3).map(goal => <li key={goal.id}><strong>{goal.name}</strong><p>{amount(goal.current_amount)} / {amount(goal.target_amount)}</p><progress value={Number(goal.current_amount)} max={Number(goal.target_amount)} aria-label={`${goal.name} savings progress`} /><small>{Number(goal.current_amount) >= Number(goal.target_amount) ? 'Goal reached' : `${Math.floor(Number(goal.current_amount) / Number(goal.target_amount) * 100)}% saved`}</small></li>)}</ul> : <div className="overview-empty"><h3>No goals yet</h3><p>Set a savings target in Budget.</p><a href="#/budget">Create a goal →</a></div>}
            {(goals.data?.length ?? 0) > 3 && <p className="overview-caption">{goals.data!.length} goals total{completedGoals > 0 ? `, ${completedGoals} reached` : ''}.</p>}
          </DashboardPanel>
          <DashboardPanel tone="rose" title="Debt progress" href="#/budget" action="View debts" loading={debts.loading} error={debts.error} onRetry={debts.retry}>
            {debts.data?.length ? <ul className="overview-progress-list">{debts.data.slice(0, 3).map(debt => <li key={debt.id}><strong>{debt.name}</strong><p>{amount(debt.remaining_amount)} remaining / {amount(debt.amount)}</p><progress value={Number(debt.current_amount)} max={Number(debt.amount)} aria-label={`${debt.name} repayment progress`} /><small>{Number(debt.remaining_amount) === 0 ? 'Paid off' : `${Math.floor(Number(debt.current_amount) / Number(debt.amount) * 100)}% repaid`}</small></li>)}</ul> : <div className="overview-empty"><h3>No debts tracked</h3><p>Add a debt to track repayments.</p><a href="#/budget">Add a debt →</a></div>}
            {(debts.data?.length ?? 0) > 3 && <p className="overview-caption">Showing 3 of {debts.data!.length} debts.</p>}
          </DashboardPanel>
        </div>
      <div className="overview-rail">
      <div className="overview-statement"><DashboardSpending /></div>
      <div className="overview-bill-summary">
        <DashboardPanel tone="sun" title="Upcoming bills" href="#/budget" action="Manage bills" loading={bills.loading} error={bills.error} onRetry={bills.retry}>
          {overdue.length > 0 && <p className="overview-alert">{overdue.length} {overdue.length === 1 ? 'bill is' : 'bills are'} overdue.</p>}
          {reminders.length ? <ul className="overview-list overview-bills">{reminders.slice(0, 3).map(bill => <li key={bill.id}><div><strong>{bill.name}</strong><small>{bill.due_date ? `${bill.due_date < today() ? 'Overdue' : bill.due_date === today() ? 'Due today' : 'Due'} · ${statementDate(bill.due_date)}` : 'No due date set'}{bill.recurring ? ' · Monthly' : ''}</small></div><strong>{amount(bill.amount)}</strong></li>)}</ul> : <div className="overview-empty"><h3>{bills.data?.length ? 'All caught up' : 'No bills yet'}</h3><p>{bills.data?.length ? 'No payments coming up.' : 'Add bills to see upcoming due dates.'}</p><a href="#/budget">Manage your bills →</a></div>}
          {reminders.length > 3 && <p className="overview-caption">Showing the next 3 of {reminders.length} bill reminders.</p>}
        </DashboardPanel>
      </div>
      </div>
      <div className="overview-accounts">
        <DashboardPanel tone="sky" title="Accounts" href="#/accounts" action="Update balances" loading={accounts.loading} error={accounts.error} onRetry={accounts.retry}>
          {accounts.data?.length ? <ul className="overview-list">{accounts.data.slice(0, 4).map(account => <li key={account.id}><div><strong>{account.name}</strong><small>{account.account_type}</small></div><strong>{amount(account.balance)}</strong></li>)}</ul> : <div className="overview-empty"><h3>No accounts yet</h3><p>Add an account to track its balance.</p><a href="#/accounts">Add your first account →</a></div>}
          {(accounts.data?.length ?? 0) > 4 && <p className="overview-caption">Showing 4 of {accounts.data!.length} accounts.</p>}
        </DashboardPanel>
      </div>
    </div>
  </div>
}
