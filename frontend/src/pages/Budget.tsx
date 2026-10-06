import { useState } from 'react'
import Paycheque from '../components/Paycheque'
import Goals from '../components/Goals'
import Debts from '../components/Debts'
import Bills from '../components/Bills'
import '../styles/budget.css'

export default function Budget() {
  const [allocationRevision, setAllocationRevision] = useState(0)
  return <div className="budget-page">
    <div className="page-intro"><span className="budget-eyebrow">Give every paycheque a purpose</span><h1>Plan your budget</h1><p>Allocate your income, build your goals, and record savings and payments. <a href="#/dashboard">See your overview →</a></p></div>
    <Paycheque onCompleted={() => setAllocationRevision(previous => previous + 1)} />
    <div className="dashboard">
      <div className="primary-workspace">
        <Goals revision={allocationRevision} />
        <Debts revision={allocationRevision} />
      </div>
      <Bills />
    </div>
  </div>
}
