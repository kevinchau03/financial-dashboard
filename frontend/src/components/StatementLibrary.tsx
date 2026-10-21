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
    <div className="statement-library-heading"><h2 id="library-heading">Saved statements</h2>{!loading && !error && <span>{total} {total === 1 ? 'file' : 'files'}</span>}</div>
    {loading ? <p role="status">Loading statements…</p> : error ? <div>
      <p role="alert">{error}</p><button type="button" className="secondary" onClick={() => setAttempt(previous => previous + 1)}>Try again</button>
    </div> : total === 0 ? <div className="statement-empty"><h3>Your first insight starts here</h3><p>Add a bank CSV to see its money in, money out, and transaction highlights.</p></div> : <>
      <ul className="statement-files">
        {statements.map((statement, index) => <li key={statement.statement_id}>
          <a href={`#/budget-wrapped?statement=${statement.statement_id}`} aria-disabled={busy || undefined} onClick={event => { if (busy) event.preventDefault() }}>
            <span className="statement-file-name">{page === 0 && index === 0 && <span className="statement-latest-label">Latest upload</span>}{statement.filename}</span>
            <span className="statement-file-meta">{statement.row_count.toLocaleString()} transactions{statement.start_date && statement.end_date && <> · {statementDate(statement.start_date)} – {statementDate(statement.end_date)}</>}</span>
            <span className="statement-file-open">Open summary</span>
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
