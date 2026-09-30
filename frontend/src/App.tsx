import Goals from './components/Goals'
import Bills from './components/Bills'
import Debts from './components/Debts'
import './App.css'

export default function App() {
  return (
    <main>
      <header>
        <p className="brand">MyBudgetPro</p>
        <h3>Financial planning made easy.</h3>
      </header>
      <div className="dashboard">
        <div className="primary-workspace">
          <Goals />
          <Debts />
        </div>
        <Bills />
      </div>
    </main>
  )
}
