import { amount, today } from '../api'
import { savingsPlan } from '../goalPlanning'
import type { Goal } from '../types'

export default function GoalPlan({ goal }: { goal: Goal }) {
  const plan = savingsPlan(goal.target_amount, goal.current_amount, goal.due_date, today())
  return <div className="goal-plan">
    {plan.status === 'funded' ? <strong>Goal funded</strong> : <>
      <strong>{amount(String(plan.remaining / 100))} left to fund</strong>
      {plan.status === 'planned' && <>
        <p>Set aside {amount(String(plan.monthly / 100))} per month to reach your target by {goal.due_date}.</p>
        <small>Estimate based on {plan.months} contributions, starting today, then monthly. Recalculates as your balance changes; no automatic transfers.</small>
      </>}
      {plan.status === 'flexible' && <p>Save at your own pace, or add a target date in Edit goal to see a monthly plan.</p>}
      {plan.status === 'past-due' && <p>Your target date has passed. Review the date or amount in Edit goal to make a new plan.</p>}
    </>}
  </div>
}
