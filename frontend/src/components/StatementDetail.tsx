import { useEffect, useRef, useState } from 'react'
import StatCard from './StatCard'
import { amount } from '../api'
import { statementDate } from '../statementTypes'
import type { StatementContents } from '../statementTypes'

export default function StatementDetail({ statementId }: { statementId: number }) {
  const [contents, setContents] = useState<StatementContents | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [page, setPage] = useState(0)
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    const controller = new AbortController()
    heading.current?.focus()
    async function load() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`/api/statements/${statementId}`, { signal: controller.signal })
        if (!response.ok) throw new Error(response.status === 404 ? 'This statement could not be found. Return to your saved statements to choose another file.' : 'Unable to load this statement. Please try again.')
        const data: StatementContents = await response.json()
        if (!controller.signal.aborted) setContents(data)
      } catch (error) {
        if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load statement.')
      } finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load()
    return () => controller.abort()
  }, [statementId, attempt])
  return <div className="statement-detail" aria-busy={loading}>
    <a className="text-link" href="#/budget-wrapped">← All saved statements</a>
    <h2 ref={heading} tabIndex={-1} className="statement-detail-title">{contents?.filename ?? 'Statement summary'}</h2>
    {loading && <p role="status">Loading your statement…</p>}
    {error && <div><p role="alert">{error}</p><button type="button" className="secondary" onClick={() => setAttempt(previous => previous + 1)}>Try again</button></div>}
    {!loading && !error && contents && <>
      <p className="statement-detail-meta">{contents.row_count.toLocaleString()} transactions · Summary for this file only</p>
      {contents.has_file ? <a className="statement-download text-link" href={`/api/statements/${statementId}/file`} download>Download original CSV</a>
        : <p className="upload-help statement-download">To download this older file, upload the same CSV again. Your saved summary will stay available.</p>}
      <section aria-label="Statement summary">
        <div className="analytics-cards">
          <StatCard tone="leaf" title="Total income" value={amount(contents.stats.total_income)} description="All credits, including transfers and refunds." />
          <StatCard tone="rose" title="Total spent" value={amount(contents.stats.total_spent)} description="All debits; credits are not subtracted." />
          <StatCard tone="sky" title="Time range" value={contents.stats.start_date && contents.stats.end_date ? `${statementDate(contents.stats.start_date)} – ${statementDate(contents.stats.end_date)}` : 'No transactions'} description="Earliest to latest transaction date." />
        </div>
      </section>
      <section aria-labelledby="csv-contents-heading">
        <h2 id="csv-contents-heading">Statement transactions</h2>
        {contents.row_count === 0 && <p>No transactions in this statement.</p>}
        <div className="csv-table-scroll" tabIndex={0} role="region" aria-label="Statement transactions table">
          <table className="csv-table"><caption>{contents.filename}</caption>
            <thead><tr>{contents.headers.map(header => <th key={header} scope="col">{header}</th>)}</tr></thead>
            <tbody>{contents.rows.slice(page * 50, (page + 1) * 50).map((row, rowIndex) => <tr key={page * 50 + rowIndex}>{row.map((value, column) => <td key={column} className={column >= 2 ? 'csv-amount' : undefined}>{column >= 2 && value !== null && value !== '' ? amount(value) : value ?? '—'}</td>)}</tr>)}</tbody>
          </table>
        </div>
        {contents.row_count > 50 && <nav className="actions" aria-label="Statement transaction pages">
          <button type="button" className="secondary" disabled={page === 0} onClick={() => setPage(previous => previous - 1)}>Previous</button>
          <span>Page {page + 1} of {Math.ceil(contents.row_count / 50)}</span>
          <button type="button" className="secondary" disabled={(page + 1) * 50 >= contents.row_count} onClick={() => setPage(previous => previous + 1)}>Next</button>
        </nav>}
      </section>
    </>}
  </div>
}

