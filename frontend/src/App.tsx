import Goals from './components/Goals'
import { useEffect, useState } from 'react'
import BudgetWrapped from './pages/BudgetWrapped'
import Analytics from './components/Analytics'
import Bills from './components/Bills'
import Debts from './components/Debts'
import './App.css'

export default function App() {
  const [page, setPage] = useState(() => window.location.hash)
  useEffect(() => {
    const navigate = () => setPage(window.location.hash)
    window.addEventListener('hashchange', navigate)
    return () => window.removeEventListener('hashchange', navigate)
  }, [])
  const wrapped = page === '#/budget-wrapped'
  const [analyticsRevision, setAnalyticsRevision] = useState(0)
  return (
    <main>
      <header>
        <p className="brand">MyBudgetPro</p>
        <h3>Financial planning made easy.</h3>
        <nav className="page-navigation" aria-label="Main navigation">
          <a href="#/" aria-current={!wrapped ? 'page' : undefined}>Dashboard</a>
          <a className="wrapped-nav-button" href="#/budget-wrapped" aria-current={wrapped ? 'page' : undefined}>
            Your Budget Wrapped <span aria-hidden="true">→</span>
          </a>
        </nav>
      </header>
      {wrapped ? <BudgetWrapped /> : <>
      <Analytics revision={analyticsRevision} />
      <div className="dashboard">
        <div className="primary-workspace">
          <Goals onSavingsChange={() => setAnalyticsRevision(previous => previous + 1)} />
          <Debts onChange={() => setAnalyticsRevision(previous => previous + 1)} />
        </div>
        <Bills onChange={() => setAnalyticsRevision(previous => previous + 1)} />
      </div>
      </>}
    </main>
  )
}

