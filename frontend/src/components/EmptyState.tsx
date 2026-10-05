export default function EmptyState({ title, description, action, onAction }: {
  title: string; description: string; action: string; onAction: () => void
}) {
  return <div className="empty-state">
    <span className="empty-state-mark" aria-hidden="true">+</span>
    <h4>{title}</h4><p>{description}</p>
    <button type="button" className="secondary" onClick={onAction}>{action}</button>
  </div>
}
