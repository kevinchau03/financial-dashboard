import CsvUpload from '../components/CsvUpload'
import StatCard from '../components/StatCard'
import { amount } from '../api'
import { useEffect, useRef, useState } from 'react'

type CsvContents = {
  filename: string; headers: string[]; rows: string[][]; row_count: number; statement_id: number; already_imported: boolean
  stats: { total_income: string; total_spent: string; start_date: string | null; end_date: string | null }
}

function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function BudgetWrapped() {
  const [file, setFile] = useState<File | null>(null)
  const [contents, setContents] = useState<CsvContents | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [page, setPage] = useState(0)
  const request = useRef<AbortController | null>(null)
  useEffect(() => () => request.current?.abort(), [])

  async function upload() {
    if (!file || request.current) return
    const controller = new AbortController()
    request.current = controller
    setLoading(true)
    setError('')
    setContents(null)
    const data = new FormData()
    data.append('file', file)
    data.append('format', 'td')
    try {
      const response = await fetch('/api/upload_csv', { method: 'POST', body: data, signal: controller.signal })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(typeof body?.detail === 'string' ? body.detail : 'Unable to upload the CSV. Please try again.')
      }
      const result: CsvContents = await response.json()
      setContents(result)
      setPage(0)
    } catch (error) {
      if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to upload CSV.')
    } finally {
      request.current = null
      if (!controller.signal.aborted) setLoading(false)
    }
  }
  return <div className="wrapped-page">
    <h1>Your Budget Wrapped</h1>
    <p className="wrapped-intro">Read your TD account activity. Upload a CSV with no header row: date (MM/DD/YYYY or YYYY-MM-DD), transaction, debit, credit, and balance.</p>
    <section aria-labelledby="upload-heading">
      <h2 id="upload-heading">Upload your TD statement</h2>
      <CsvUpload disabled={loading} onFileSelect={selected => { setFile(selected); setContents(null); setError(''); setPage(0) }} />
      <div className="actions"><button type="button" disabled={!file || loading} onClick={upload}>{loading ? 'Uploading…' : 'Upload CSV'}</button></div>
      {error && <p role="alert">{error}</p>}
      <p role="status">{loading ? 'Saving your statement…' : contents ? contents.already_imported ? `This file was already saved. Showing ${contents.row_count} transactions from ${contents.filename}.` : `Saved ${contents.row_count} transactions from ${contents.filename}.` : ''}</p>
    </section>
    {contents && <section aria-labelledby="statement-summary-heading">
      <h2 id="statement-summary-heading">Your statement summary</h2>
      <p>Across all saved statements.</p>
      <div className="analytics-cards">
        <StatCard title="Total income" value={amount(contents.stats.total_income)} description="All credits, including transfers and refunds." />
        <StatCard title="Total spent" value={amount(contents.stats.total_spent)} description="All debits; credits are not subtracted." />
        <StatCard title="Time range" value={contents.stats.start_date && contents.stats.end_date
          ? `${formatDate(contents.stats.start_date)} – ${formatDate(contents.stats.end_date)}` : 'No transactions'}
          description="Earliest to latest transaction date." />
      </div>
    </section>}
    {contents && <section aria-labelledby="csv-contents-heading">
      <h2 id="csv-contents-heading">Statement transactions</h2>
      {contents.row_count === 0 && <p>This CSV has headers but no data rows.</p>}
      <div className="csv-table-scroll" tabIndex={0} role="region" aria-label="CSV contents table">
        <table className="csv-table"><caption>{contents.filename}</caption>
          <thead><tr>{contents.headers.map((header, index) => <th key={index} scope="col">{header || `Column ${index + 1}`}</th>)}</tr></thead>
          <tbody>{contents.rows.slice(page * 50, (page + 1) * 50).map((row, rowIndex) => <tr key={page * 50 + rowIndex}>{row.map((value, column) => <td key={column} className={column >= 2 ? 'csv-amount' : undefined}>{value || '—'}</td>)}</tr>)}</tbody>
        </table>
      </div>
      {contents.row_count > 50 && <nav className="actions" aria-label="CSV pages">
        <button type="button" disabled={page === 0} onClick={() => setPage(previous => previous - 1)}>Previous</button>
        <span>Page {page + 1} of {Math.ceil(contents.row_count / 50)}</span>
        <button type="button" disabled={(page + 1) * 50 >= contents.row_count} onClick={() => setPage(previous => previous + 1)}>Next</button>
      </nav>}
    </section>}
  </div>
}
