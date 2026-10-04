import type { ReactNode } from 'react'

export default function CollapsibleItem({ title, summary, progress, target, progressLabel, children }: {
  title: string
  summary: ReactNode
  progress: number
  target: number
  progressLabel: string
  children: ReactNode
}) {
  return <details className="collapsible-item">
    <summary className="item-summary">
      <span className="item-title">{title}<span className="item-chevron" aria-hidden="true">›</span></span>
      <span className="item-balance">{summary}</span>
      <progress aria-label={progressLabel} value={Math.min(progress, target)} max={target} />
    </summary>
    <div className="item-content">{children}</div>
  </details>
}
