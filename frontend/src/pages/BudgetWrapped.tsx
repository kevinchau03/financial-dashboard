import CsvUpload from '../components/CsvUpload'
import StatementLibrary from '../components/StatementLibrary'
import StatementDetail from '../components/StatementDetail'
import { useEffect, useRef, useState } from 'react'
import useHash from '../hooks/useHash'
import { statementIdFromHash } from '../routing'
import '../styles/statements.css'

export default function BudgetWrapped() {
  const statementId = statementIdFromHash(useHash())
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const request = useRef<AbortController | null>(null)
  const pageHeading = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    const navigate = () => {
      request.current?.abort()
      request.current = null
      setLoading(false)
      setFile(null)
      setError('')
      window.scrollTo(0, 0)
      if (statementIdFromHash(window.location.hash) === null) pageHeading.current?.focus({ preventScroll: true })
    }
    window.addEventListener('hashchange', navigate)
    return () => { window.removeEventListener('hashchange', navigate); request.current?.abort() }
  }, [])

  async function upload() {
    if (!file || request.current) return
    const controller = new AbortController()
    request.current = controller
    setLoading(true)
    setError('')
    const data = new FormData()
    data.append('file', file)
    data.append('format', 'td')
    try {
      const response = await fetch('/api/upload_csv', { method: 'POST', body: data, signal: controller.signal })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(typeof body?.detail === 'string' ? body.detail : 'Unable to upload the CSV. Please try again.')
      }
      const result: { statement_id: number } = await response.json()
      if (!controller.signal.aborted) {
        setFile(null)
        window.location.hash = `/budget-wrapped?statement=${result.statement_id}`
      }
    } catch (error) {
      if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Unable to upload CSV.')
    } finally {
      if (request.current === controller) request.current = null
      if (!controller.signal.aborted) setLoading(false)
    }
  }
  return <div className="wrapped-page">
    <h1 ref={pageHeading} tabIndex={-1}>Your Budget Wrapped</h1>
    {statementId !== null ? <StatementDetail key={statementId} statementId={statementId} /> : <>
      <p className="wrapped-intro">Your statements, one at a time. Save a TD CSV and revisit its spending summary whenever you like.</p>
      <StatementLibrary busy={loading} />
      <section aria-labelledby="upload-heading" aria-busy={loading}>
        <h2 id="upload-heading">Upload a statement</h2>
        <p className="upload-help">Use a TD CSV with no header row: date (MM/DD/YYYY or YYYY-MM-DD), transaction, debit, credit, and balance.</p>
        <CsvUpload disabled={loading} onFileSelect={selected => { setFile(selected); setError('') }} />
        <div className="actions"><button type="button" disabled={!file || loading} onClick={upload}>{loading ? 'Saving…' : 'Save statement'}</button></div>
        {error && <p role="alert">{error}</p>}
        <p role="status">{loading ? 'Saving your statement. Its summary will open when ready.' : ''}</p>
      </section>
    </>}
  </div>
}
