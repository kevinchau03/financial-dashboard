export default function Home() {
  return <div className="home-page">
    <div className="home-hero">
      <p className="brand">A little clarity. A little progress.</p>
      <h1>Make room for the life you’re saving for.</h1>
      <p>MyBudgetPro brings your savings goals, debts, bills, and account balances into a calmer place. Start small and build a plan that makes sense to you.</p>
      <div className="actions"><a className="button-link" href="#/budget">Start your budget</a><a className="text-link" href="#/budget-wrapped">Explore your spending →</a></div>
    </div>
    <div className="feature-grid">
      <section><p className="brand">01 · PLAN</p><h2>Give your money a purpose</h2><p>Save for a trip, work toward a new car, pay down debt, and keep upcoming bills close by.</p><a href="#/budget">Go to Budget →</a></section>
      <section><p className="brand">02 · REFLECT</p><h2>Your Budget Wrapped</h2><p>Turn your TD CSV statements into an easy-to-read view of money in, money out, and the transactions behind it.</p><a href="#/budget-wrapped">Review your statements →</a></section>
      <section><p className="brand">03 · KEEP TRACK</p><h2>See where your money lives</h2><p>Keep your savings, chequing, TFSA, FHSA, and other balances together with simple manual updates.</p><a href="#/accounts">View your accounts →</a></section>
    </div>
  </div>
}
