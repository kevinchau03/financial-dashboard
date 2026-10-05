import { useEffect, useId, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { unsavedForms } from '../unsavedForms'

export default function Modal({ title, busy = false, onClose, children }: {
  title: string; busy?: boolean; onClose: () => void; children: ReactNode
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const [confirmClose, setConfirmClose] = useState(false)
  function requestClose() {
    if (busy) return
    const dirty = [...(dialog.current?.querySelectorAll('form') ?? [])].some(form => unsavedForms.get(form)?.().dirty)
    if (dirty) setConfirmClose(true)
    else onClose()
  }
  useEffect(() => {
    if (confirmClose) dialog.current?.querySelector<HTMLButtonElement>('[data-keep-editing]')?.focus()
  }, [confirmClose])
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
    if (confirmClose) setConfirmClose(false)
    else requestClose()
  }}>
    <div className="modal-heading">
      <h2 id={titleId}>{title}</h2>
      <button type="button" className="secondary" disabled={busy} onClick={requestClose} aria-label={`Close ${title}`}>Close</button>
    </div>
    <div hidden={confirmClose}>{children}</div>
    {confirmClose && <div role="alert" className="discard-prompt">
      <p>Your changes have not been saved. Discard them?</p>
      <div className="actions">
        <button type="button" className="secondary" data-keep-editing onClick={() => {
          setConfirmClose(false)
          requestAnimationFrame(() => dialog.current?.querySelector<HTMLInputElement>('input')?.focus())
        }}>Keep editing</button>
        <button type="button" className="danger" onClick={onClose}>Discard changes</button>
      </div>
    </div>}
  </dialog>
}
