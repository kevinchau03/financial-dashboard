export default function Notice({ message }: { message: string }) {
  return <div className="notice-anchor">
    <span className="inline-notice" role="status" aria-live="polite" aria-atomic="true">{message}</span>
  </div>
}
