import { useState } from 'react'
import Analytics from '../components/Analytics'
import Paycheque from '../components/Paycheque'
import Goals from '../components/Goals'
import Debts from '../components/Debts'
import Bills from '../components/Bills'
import '../styles/budget.css'

export default function Budget() {
  const [revision, setRevision] = useState(0)
  const refresh = () => setRevision(previous => previous + 1)
  return <div className="budget-page">
    <div className="page-intro"><span className="budget-eyebrow">A little progress, every day</span><h1>Your budget</h1><p>Give your savings a purpose. Make room for what comes next.</p></div>
    <Analytics revision={revision} />
    <Paycheque />
    <div className="dashboard">
      <div className="primary-workspace">
        <Goals onSavingsChange={refresh} />
        <Debts onChange={refresh} />
      </div>
      <Bills onChange={refresh} />
    </div>
  </div>
}
