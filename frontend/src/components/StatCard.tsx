type StatCardProps = {
  title: string
  value: string
  description?: string
  loading?: boolean
  error?: string
  onRetry?: () => void
}

export default function StatCard({ title, value, description, loading, error, onRetry }: StatCardProps) {
  return <section className="stat-card" aria-label={title} aria-busy={loading}>
    <h2>{title}</h2>
    <div aria-live="polite">
      {loading ? <p className="stat-value">Loading…</p> : error ? <>
        <p role="alert">{error}</p>
        {onRetry && <button type="button" className="secondary" onClick={onRetry}>Retry</button>}
      </> : <p className="stat-value">{value}</p>}
    </div>
    {description && <p className="stat-description">{description}</p>}
  </section>
}
