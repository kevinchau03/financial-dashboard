import type { ReactNode } from 'react'
import type { CardTone } from '../types'

export default function DashboardPanel({ title, href, action, loading, error, onRetry, children, tone }: {
  tone?: CardTone
  title: string; href: string; action: string; loading: boolean; error: string; onRetry: () => void; children: ReactNode
}) {
  return <section className="overview-panel" data-tone={tone} aria-label={title} aria-busy={loading}>
    <div className="overview-heading"><h2>{title}</h2><a href={href}>{action} <span aria-hidden="true">→</span></a></div>
    {loading ? <p role="status">Loading {title.toLowerCase()}…</p> : error ? <div><p role="alert">{error}</p><button type="button" className="secondary" onClick={onRetry}>Retry</button></div> : children}
  </section>
}
