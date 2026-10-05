import Home from './pages/Home'
import Budget from './pages/Budget'
import BudgetWrapped from './pages/BudgetWrapped'
import Accounts from './pages/Accounts'
import Navigation from './components/Navigation'
import UnsavedChanges from './components/UnsavedChanges'
import usePage from './hooks/usePage'
import './App.css'

export default function App() {
  const path = usePage()
  return <div className={path === '#/' ? 'site-layout' : 'site-layout with-sidebar'}>
    <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus() }}>Skip to content</a>
    <Navigation path={path} />
    <UnsavedChanges />
    <main id="main-content" tabIndex={-1}>
      {path === '#/' ? <Home /> : path === '#/budget' ? <Budget /> : path === '#/budget-wrapped' ? <BudgetWrapped /> : path === '#/accounts' ? <Accounts /> : <div className="page-intro"><h1>Page not found</h1><a href="#/">Return home</a></div>}
    </main>
      <footer>
        <p>MyBudgetPro is a free, open-source project. <a href="https://github.com/mybudgetpro/mybudgetpro" target="_blank" rel="noopener noreferrer">Contribute on GitHub</a></p>
      </footer>
  </div>
}
