import { apiFetch } from '../auth'
import { useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import { amount } from '../api'
import { statementDate } from '../statementTypes'
import { transactionOccurrences } from '../statementInsights'

// Playful statement labels, based on money movement rather than verified earnings
// or savings. Rules are evaluated in order so every overspending statement matches
// Big Spender, including those only slightly above money in.
const titles = [
  {
    name: 'Big Spender',
    description: 'More money went out than came in during this statement.',
    matches: (income: number, expenses: number) => expenses > income,
  },
  {
    name: 'Sally Saves A Lot',
    description: 'Money out was no more than half of money in during this statement.',
    matches: (income: number, expenses: number) => income > 0 && expenses >= 0 && expenses <= income * 0.5,
  },
  {
    name: 'Mr. Come and Go',
    description: 'Money out was within 10% of money in during this statement.',
    matches: (income: number, expenses: number) => income > 0 && expenses >= income * 0.9 && expenses <= income,
  },
  {
    name: 'Steady Saver',
    description: 'Money out was more than half, but less than 90%, of money in during this statement.',
    matches: (income: number, expenses: number) => income > 0 && expenses > income * 0.5 && expenses < income * 0.9,
  },
  {
    name: 'All Quiet on the Budget Front',
    description: 'No money moved in or out during this statement.',
    matches: (income: number, expenses: number) => income === 0 && expenses === 0,
  },
] as const

type Insights = {
  statement_id: number; start_date: string | null; end_date: string | null
  total_income: string; total_spent: string; total_transactions: number
  most_frequent_transaction_name: string | null
  most_frequent_transaction_count?: number
  largest_transaction: { id: number; date: string; description: string; amount: string; kind: 'debit' | 'credit' } | null
  highest_spending_day: { date: string; total_spent: string; transactions: { id: number; description: string; debit: string | null; credit: string | null }[] } | null
}

export default function StatementWrapped({ statementId, filename, transactions, onClose, onReviewTransactions }: {
  statementId: number; filename: string; transactions: (string | null)[][]; onClose: () => void; onReviewTransactions: () => void
}) {
  const [insights, setInsights] = useState<Insights | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [step, setStep] = useState(0)
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await apiFetch(`/api/statements/${statementId}/insights`, { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load your Wrapped. Try again or view the statement summary.')
        const data: Insights = await response.json()
        if (!controller.signal.aborted) setInsights(data)
      } catch (error) { if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load insights.') }
    }
    void load()
    return () => controller.abort()
  }, [statementId, attempt])
  useEffect(() => { heading.current?.focus() }, [step, insights, error])
  const statementTitle = insights ? titles.find(title => title.matches(Number(insights.total_income), Number(insights.total_spent))) : undefined
  const slides = insights ? [
    { title: 'Your statement has a personality.', label: 'Your title', value: statementTitle?.name ?? 'A Different Kind of Month', note: `${statementTitle?.description ?? 'This statement has an unusual mix of credits and debits.'} This playful title is based on this file only, including transfers and refunds; it does not measure actual earnings or savings.` },
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
    <p className="wrapped-file" title={filename}>{filename}</p>
    {!insights ? error ? <div role="alert"><h2 ref={heading} tabIndex={-1}>Your recap is taking a rain check.</h2><p>{error}</p><button type="button" onClick={() => { setError(''); setAttempt(value => value + 1) }}>Try again</button></div> : <p role="status">Gathering your statement highlights...</p> : <>
      <p className="wrapped-period">{insights.start_date && insights.end_date ? `${statementDate(insights.start_date)} - ${statementDate(insights.end_date)}` : 'This statement has no transactions'}</p>
      <ol className="wrapped-progress" aria-label="Recap screens">{slides.map((item, index) => <li key={item.label}><button type="button" aria-current={index === step ? 'step' : undefined} aria-label={`Screen ${index + 1}: ${item.label}`} onClick={() => setStep(index)}><span className="sr-only">{index + 1}</span></button></li>)}</ol>
      <div className="wrapped-slide" key={step}>
        {step === 0 && <div className="wrapped-confetti" aria-hidden="true">{Array.from({ length: 48 }, (_, index) => <span key={index} style={{ '--confetti-x': `${(index * 37) % 100}%`, '--confetti-delay': `${(index % 8) * 0.06}s`, '--confetti-drift': `${((index * 29) % 180) - 90}px`, '--confetti-turn': `${180 + (index % 5) * 120}deg` } as CSSProperties} />)}</div>}
        <p className="wrapped-screen-count">{step + 1} / {slides.length}</p>
        <h2 ref={heading} tabIndex={-1}>{slide.title}</h2>
        <p className="wrapped-metric-label">{slide.label}</p>
        <p className="wrapped-metric">{slide.value}</p>
        <p className="wrapped-explanation">{slide.note}</p>
        {step === 4 && insights.most_frequent_transaction_name !== null && <p className="wrapped-frequency">Appeared <strong>{occurrences.toLocaleString()} {occurrences === 1 ? 'time' : 'times'}</strong> in this statement.</p>}
        {step === 5 && insights.largest_transaction && <div className="wrapped-transaction-detail">
          <strong>{insights.largest_transaction.kind === 'debit' ? 'Debit - money out' : 'Credit - money in'}</strong>
          <p>{insights.largest_transaction.description}</p>
          <time dateTime={insights.largest_transaction.date}>{statementDate(insights.largest_transaction.date)}</time>
        </div>}
        {step === 6 && insights.highest_spending_day && <div className="wrapped-day-detail">
          <h3>{amount(insights.highest_spending_day.total_spent)} spent that day</h3>
          <button type="button" className="secondary" onClick={onReviewTransactions}>Review transactions in summary</button>
        </div>}

      </div>
      <div className="wrapped-player-controls"><button type="button" className="secondary" disabled={step === 0} onClick={() => setStep(value => value - 1)}>Back</button><button type="button" onClick={() => { if (step === slides.length - 1) onClose(); else setStep(value => value + 1) }}>{step === slides.length - 1 ? 'Finish - view summary' : 'Next insight'}</button></div>
    </>}
  </section>
}
