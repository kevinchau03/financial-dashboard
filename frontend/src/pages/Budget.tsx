import Paycheque from '../components/Paycheque'
import Goals from '../components/Goals'
import Debts from '../components/Debts'
import Bills from '../components/Bills'
import '../styles/budget.css'

export default function Budget() {
  return <div className="budget-page">
    <div className="budget-header">
      <div className="page-intro"><span className="budget-eyebrow">Give every paycheque a purpose</span><h1>Plan your budget</h1></div>
      <Paycheque />
    </div>
    <div className="dashboard">
      <div className="primary-workspace">
        <Goals revision={0} />
        <Debts revision={0} />
      </div>
      <Bills />
    </div>
  </div>
}
