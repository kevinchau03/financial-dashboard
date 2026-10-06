import { useEffect, useState } from 'react'
import type { SavedStatement } from '../statementTypes'
import { statementDate } from '../statementTypes'

export default function StatementLibrary({ busy }: { busy: boolean }) {
  const [statements, setStatements] = useState<SavedStatement[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const pageSize = 20
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`/api/statements?offset=${page * pageSize}&limit=${pageSize}`, { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load saved statements. Please try again.')
        const data: { items: SavedStatement[]; total: number } = await response.json()
        if (!controller.signal.aborted) { setStatements(data.items); setTotal(data.total) }
      } catch (error) {
        if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to load saved statements.')
      } finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load()
    return () => controller.abort()
  }, [page, attempt])
  return <section aria-labelledby="library-heading" aria-busy={loading} className="statement-library">
    <h2 id="library-heading">Your saved statements</h2>
    <p className="upload-help">Open a file to see its own spending, income, and transactions.</p>
    {loading ? <p role="status">Loading statements…</p> : error ? <div>
      <p role="alert">{error}</p><button type="button" className="secondary" onClick={() => setAttempt(previous => previous + 1)}>Try again</button>
    </div> : total === 0 ? <p className="statement-empty">No statements saved yet. Upload your first TD CSV below to start your collection.</p> : <>
      <ul className="statement-files">
        {statements.map(statement => <li key={statement.statement_id}>
          <a href={`#/budget-wrapped?statement=${statement.statement_id}`} aria-disabled={busy || undefined} onClick={event => { if (busy) event.preventDefault() }}>
            <span className="statement-file-name">{statement.filename}</span>
            <span className="statement-file-meta">{statement.row_count.toLocaleString()} transactions{statement.start_date && statement.end_date && <> · {statementDate(statement.start_date)} – {statementDate(statement.end_date)}</>}</span>
            <span className="statement-file-open">View statement <span aria-hidden="true">→</span></span>
          </a>
        </li>)}
      </ul>
      {total > pageSize && <nav className="actions" aria-label="Saved statement pages">
        <button type="button" className="secondary" disabled={page === 0 || busy} onClick={() => setPage(previous => previous - 1)}>Previous</button>
        <span>Page {page + 1} of {Math.ceil(total / pageSize)}</span>
        <button type="button" className="secondary" disabled={(page + 1) * pageSize >= total || busy} onClick={() => setPage(previous => previous + 1)}>Next</button>
      </nav>}
    </>}
  </section>
}
