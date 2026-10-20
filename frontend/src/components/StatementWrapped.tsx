import { useEffect, useRef, useState } from 'react'
import { amount } from '../api'
import { statementDate } from '../statementTypes'
import { transactionOccurrences } from '../statementInsights'

type Insights = {
  statement_id: number; start_date: string | null; end_date: string | null
  total_income: string; total_spent: string; total_transactions: number
  most_frequent_transaction_name: string | null
  most_frequent_transaction_count?: number
  largest_transaction: { id: number; date: string; description: string; amount: string; kind: 'debit' | 'credit' } | null
  highest_spending_day: { date: string; total_spent: string; transactions: { id: number; description: string; debit: string | null; credit: string | null }[] } | null
}

export default function StatementWrapped({ statementId, filename, transactions, onClose }: {
  statementId: number; filename: string; transactions: (string | null)[][]; onClose: () => void
}) {
  const [insights, setInsights] = useState<Insights | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [step, setStep] = useState(0)
  const [dayPage, setDayPage] = useState(0)
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await fetch(`/api/statements/${statementId}/insights`, { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load your Wrapped. Try again or view the statement summary.')
        const data: Insights = await response.json()
        if (!controller.signal.aborted) setInsights(data)
      } catch (error) { if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load insights.') }
    }
    void load()
    return () => controller.abort()
  }, [statementId, attempt])
  useEffect(() => { heading.current?.focus() }, [step, insights, error])
  const slides = insights ? [
    { title: 'Money made its entrance.', label: 'Money in', value: amount(insights.total_income), note: 'All credits in this statement, including transfers and refunds. Not all money in is earnings.' },
    { title: 'And money went places.', label: 'Money out', value: amount(insights.total_spent), note: 'All debits in this statement, including transfers and fees. Credits are not subtracted.' },
    { title: 'Little moments. One bigger picture.', label: 'Transactions recorded', value: insights.total_transactions.toLocaleString(), note: 'Every transaction in this file counts, whether money came in or went out.' },
    { title: 'A familiar name in your statement.', label: 'Most frequent transaction name', value: insights.most_frequent_transaction_name ?? 'No transactions yet', note: 'Grouped by the exact bank description, across debits and credits. Different descriptions may refer to the same merchant.' },
    { title: 'The biggest single movement.', label: 'Largest transaction', value: insights.largest_transaction === null ? 'No transactions yet' : amount(insights.largest_transaction.amount), note: 'The largest individual debit or credit. This could be a paycheque, transfer, or purchase.' },
    { title: 'The day money moved out most.', label: 'Highest-spending day', value: insights.highest_spending_day ? statementDate(insights.highest_spending_day.date) : 'No spending recorded', note: 'The date with the highest total positive debits. Transfers and fees can be included. That is your statement, wrapped.' },
  ] : []
  const slide = slides[step]
  const occurrences = insights ? transactionOccurrences(insights.most_frequent_transaction_name, insights.most_frequent_transaction_count, transactions) : 0
  return <section className={`statement-wrapped wrapped-tone-${step % 3}`} aria-label="Your Budget Wrapped player" aria-busy={!insights && !error}>
    <div className="wrapped-player-heading"><span>Your Budget Wrapped</span><button type="button" className="secondary" onClick={onClose}>View summary</button></div>
    <p className="wrapped-file">{filename}</p>
    {!insights ? error ? <div role="alert"><h2 ref={heading} tabIndex={-1}>Your recap is taking a rain check.</h2><p>{error}</p><button type="button" onClick={() => { setError(''); setAttempt(value => value + 1) }}>Try again</button></div> : <p role="status">Gathering your statement highlights...</p> : <>
      <p className="wrapped-period">{insights.start_date && insights.end_date ? `${statementDate(insights.start_date)} - ${statementDate(insights.end_date)}` : 'This statement has no transactions'}</p>
      <ol className="wrapped-progress" aria-label="Recap screens">{slides.map((item, index) => <li key={item.label}><button type="button" aria-current={index === step ? 'step' : undefined} aria-label={`Screen ${index + 1}: ${item.label}`} onClick={() => setStep(index)}><span className="sr-only">{index + 1}</span></button></li>)}</ol>
      <div className="wrapped-slide" key={step}>
        <p className="wrapped-screen-count">{step + 1} / 6</p>
        <h2 ref={heading} tabIndex={-1}>{slide.title}</h2>
        <p className="wrapped-metric-label">{slide.label}</p>
        <p className="wrapped-metric">{slide.value}</p>
        <p className="wrapped-explanation">{slide.note}</p>
        {step === 3 && insights.most_frequent_transaction_name !== null && <p className="wrapped-frequency">Appeared <strong>{occurrences.toLocaleString()} {occurrences === 1 ? 'time' : 'times'}</strong> in this statement.</p>}
        {step === 4 && insights.largest_transaction && <div className="wrapped-transaction-detail">
          <strong>{insights.largest_transaction.kind === 'debit' ? 'Debit - money out' : 'Credit - money in'}</strong>
          <p>{insights.largest_transaction.description}</p>
          <time dateTime={insights.largest_transaction.date}>{statementDate(insights.largest_transaction.date)}</time>
        </div>}
        {step === 5 && insights.highest_spending_day && <div className="wrapped-day-detail">
          <h3>{amount(insights.highest_spending_day.total_spent)} spent that day</h3>
          <p>All transactions on this date. Credits are shown separately and do not reduce the spending total.</p>
          <div className="csv-table-scroll" tabIndex={0} role="region" aria-label="Transactions on the highest-spending day">
            <table className="csv-table"><caption>Transactions on {statementDate(insights.highest_spending_day.date)}</caption>
              <thead><tr><th scope="col">Transaction</th><th scope="col">Debit (out)</th><th scope="col">Credit (in)</th></tr></thead>
              <tbody>{insights.highest_spending_day.transactions.slice(dayPage * 10, (dayPage + 1) * 10).map(transaction => <tr key={transaction.id}><td>{transaction.description}</td><td className="csv-amount">{transaction.debit === null ? '-' : amount(transaction.debit)}</td><td className="csv-amount">{transaction.credit === null ? '-' : amount(transaction.credit)}</td></tr>)}</tbody>
            </table>
          </div>
          {insights.highest_spending_day.transactions.length > 10 && <nav className="actions" aria-label="Spending day transaction pages"><button type="button" className="secondary" disabled={dayPage === 0} onClick={() => setDayPage(value => value - 1)}>Previous transactions</button><span>Page {dayPage + 1} of {Math.ceil(insights.highest_spending_day.transactions.length / 10)}</span><button type="button" className="secondary" disabled={(dayPage + 1) * 10 >= insights.highest_spending_day.transactions.length} onClick={() => setDayPage(value => value + 1)}>Next transactions</button></nav>}
        </div>}

      </div>
      <div className="wrapped-player-controls"><button type="button" className="secondary" disabled={step === 0} onClick={() => setStep(value => value - 1)}>Back</button><button type="button" onClick={() => { if (step === 5) onClose(); else setStep(value => value + 1) }}>{step === 5 ? 'Finish - view summary' : 'Next insight'}</button></div>
    </>}
  </section>
}
