import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'

export default function Modal({ title, busy = false, onClose, children }: {
  title: string; busy?: boolean; onClose: () => void; children: ReactNode
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  useEffect(() => {
    const element = dialog.current!
    const trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const overflow = document.body.style.overflow
    element.showModal()
    element.querySelector<HTMLInputElement>('input')?.focus()
    document.body.style.overflow = 'hidden'
    return () => {
      element.close()
      document.body.style.overflow = overflow
      trigger?.focus()
    }
  }, [])
  return <dialog ref={dialog} className="modal" aria-labelledby={titleId} onCancel={event => {
    event.preventDefault()
    if (!busy) onClose()
  }}>
    <div className="modal-heading">
      <h2 id={titleId}>{title}</h2>
      <button type="button" className="secondary" disabled={busy} onClick={onClose} aria-label={`Close ${title}`}>Close</button>
    </div>
    {children}
  </dialog>
}
