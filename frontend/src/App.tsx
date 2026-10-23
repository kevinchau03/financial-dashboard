import { useState } from 'react'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Budget from './pages/Budget'
import PaychequePlanner from './pages/PaychequePlanner'
import BudgetWrapped from './pages/BudgetWrapped'
import Accounts from './pages/Accounts'
import Activity from './pages/Activity'
import Navigation from './components/Navigation'
import UnsavedChanges from './components/UnsavedChanges'
import usePage from './hooks/usePage'
import AuthGate from './components/AuthGate'
import './App.css'
import './styles/colors.css'

export default function App() {
  return <AuthGate><AuthenticatedApp /></AuthGate>
}

function AuthenticatedApp() {
  const path = usePage()
  const [navigationCollapsed, setNavigationCollapsed] = useState(false)
  const hasSidebar = path !== '#/'

  return <div className={hasSidebar ? `site-layout with-sidebar${navigationCollapsed ? ' sidebar-collapsed' : ''}` : 'site-layout'}>
    <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus() }}>Skip to content</a>
    <Navigation path={path} collapsed={navigationCollapsed} onToggle={() => setNavigationCollapsed(value => !value)} />
    <UnsavedChanges />
    <main id="main-content" tabIndex={-1}>
      {path === '#/' ? <Home /> : path === '#/dashboard' ? <Dashboard /> : path === '#/budget' ? <Budget /> : path === '#/budget/paycheques' ? <PaychequePlanner /> : path === '#/budget-wrapped' ? <BudgetWrapped /> : path === '#/accounts' ? <Accounts /> : path === '#/activity' ? <Activity /> : <div className="page-intro"><h1>Page not found</h1><a href="#/dashboard">Go to Dashboard</a></div>}
    </main>
      <footer>
        <p>MyBudgetPro is a free, open-source project. <a href="https://github.com/mybudgetpro/mybudgetpro" target="_blank" rel="noopener noreferrer">Contribute on GitHub</a></p>
      </footer>
  </div>
}
