import '../styles/learn.css'

const features = [
  {
    title: 'Create savings goals',
    description: 'Give each goal a name, a target amount, and an optional target date. Track your progress and see a monthly savings estimate for future targets. You can also link a goal to an account to earmark money for it.',
    href: '#/budget',
    linkLabel: 'Create a goal in Budget',
  },
  {
    title: 'Create debt records',
    description: 'Add the debts you want to pay off, then record payments as you make them. Watch the remaining balance decrease and review your payment history. Once a debt is paid off, resolve it to remove it from your active list.',
    href: '#/budget',
    linkLabel: 'Add a debt in Budget',
  },
  {
    title: 'Manage bills',
    description: 'Add bills in Budget with their amounts and due dates so you can see what is coming up. Record a payment after you pay a bill. Monthly recurring bills advance to their next due date when a payment is recorded; one-time bills stay marked as paid.',
    href: '#/budget',
    linkLabel: 'Manage bills in Budget',
  },
  {
    title: 'Paycheque planner',
    description: 'Enter your take-home pay, reserve money for bills and everyday spending, then allocate the rest to goals, debts, or accounts. Saving a plan does not change recorded balances. After you save or pay the money yourself, record the allocation as completed. A linked goal allocation updates both the goal and its account, so allocate that deposit to the goal only.',
    href: '#/budget/paycheques',
    linkLabel: 'Open Paycheque planner',
  },
  {
    title: 'Your Budget Wrapped',
    description: 'Upload a supported transaction CSV to see a summary of that file, then play an optional recap of money in, money out, transaction counts, and notable transactions. Review the transaction table or reopen a saved file later. Transfers can appear in money in and money out, so these totals are not a measure of income, spending, or savings on their own.',
    href: '#/budget-wrapped',
    linkLabel: 'Open Your Budget Wrapped',
  },
]

export default function Learn() {
  return <div className="learn-page">
    <div className="page-intro">
      <h1>Learn</h1>
      <p>Get to know MyBudgetPro, from your starting point to your first plan.</p>
      <p>MyBudgetPro helps you plan and record your finances. You make transfers and payments yourself through your bank; the app does not move money or pay bills.</p>
    </div>

    <div className="learn-sections">
      <section className="learn-section" aria-labelledby="learn-user-title">
        <span className="learn-step" aria-hidden="true">1</span>
        <div className="learn-section-body">
          <h2 id="learn-user-title">Who This App Is For</h2>
          <p>This app is for you if you:</p>
          <ol>
            <li>Want to get your finances in order.</li>
            <li>Have several financial goals to work toward.</li>
            <li>Like keeping your budget, goals, and financial records in one place.</li>
            <li>Enjoy a sleek interface with a distinct look and feel.</li>
          </ol>
        </div>
      </section>

      <section className="learn-section" aria-labelledby="learn-method-title">
        <span className="learn-step" aria-hidden="true">2</span>
        <div className="learn-section-body">
          <h2 id="learn-method-title">The sinking fund method</h2>
          <p>The sinking fund method means setting aside small, regular amounts of money for a specific future expense, such as Christmas gifts or a vacation.</p>
          <p>MyBudgetPro helps you plan and track these savings, giving your money a purpose and helping you work toward what matters to you.</p>
          <h3>A simple setup order</h3>
          <ol className="learn-example">
            <li><strong>Add an account.</strong> Open <a href="#/accounts">Accounts</a> and enter the balance you want to track.</li>
            <li><strong>Give your money a purpose.</strong> In <a href="#/budget">Budget</a>, create your goals, add your debts, and list your bills. Link goals to an account when you want to earmark part of its balance.</li>
            <li><strong>Plan your next paycheque.</strong> Use <a href="#/budget/paycheques">Paycheque planner</a> to reserve everyday spending and bill money, then allocate what is left. Record allocations as completed after you save or pay the money yourself.</li>
          </ol>
          <p>You can read this guide without an account. <a href="#/sign-up">Sign up</a> or <a href="#/sign-in">sign in</a> when you are ready to use the tools.</p>
        </div>
      </section>

      <section className="learn-section" aria-labelledby="learn-features-title">
        <span className="learn-step" aria-hidden="true">3</span>
        <div className="learn-section-body">
          <h2 id="learn-features-title">Explore the features</h2>
          <p>Learn what each tool does and how to use it.</p>
          <ul className="learn-features">
            {features.map(feature => <li key={feature.title}>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
              <a className="learn-feature-link" href={feature.href}>{feature.linkLabel}</a>
            </li>)}
          </ul>
        </div>
      </section>

      <section className="learn-section" aria-labelledby="learn-example-title">
        <span className="learn-step" aria-hidden="true">4</span>
        <div className="learn-section-body">
          <h2 id="learn-example-title">See it in practice</h2>
          <p>Imagine you want to save $600 for a vacation over your next six paycheques. Starting from $0, that means setting aside $100 from each paycheque. Here is how you could track it in MyBudgetPro.</p>
          <ol className="learn-example">
            <li><strong>Add your account.</strong> In Accounts, add a savings account with a recorded balance of $0.</li>
            <li><strong>Create your goal.</strong> In Budget, add a Vacation goal with a $600 target and $0 saved. Link it to your savings account. You can add a target date to see a monthly estimate; this example uses $100 per paycheque instead.</li>
            <li><strong>Plan your paycheque.</strong> Open Paycheque planner and enter $1,500 in take-home pay. Reserve $1,000 for bills and $300 for everyday spending, then allocate $100 to Vacation. That leaves $100 unallocated. Saving the plan leaves your recorded savings at $0.</li>
            <li><strong>Save, then record it.</strong> Transfer $100 to your savings account through your bank. Return to the saved plan and record the Vacation allocation as completed. The app now shows $100 saved toward Vacation and a $100 account balance. These are the same $100, so do not add another account allocation or manually increase the balance for that deposit.</li>
            <li><strong>Repeat and review.</strong> Follow the same steps for your next five paycheques. With no withdrawals or other changes, your goal and account will each show $600. Check your progress on Dashboard and your recorded contributions in Activity history.</li>
          </ol>
          <p>The same idea works for gifts, annual expenses, or other goals: give each one a target, decide what to set aside, and record your progress as you go.</p>
        </div>
      </section>
    </div>
  </div>
}
