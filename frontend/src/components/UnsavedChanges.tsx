import { useEffect, useRef, useState } from 'react'
import Modal from './Modal'
import { unsavedForms } from '../unsavedForms'

export default function UnsavedChanges() {
  const [destination, setDestination] = useState<HTMLElement | null>(null)
  const approved = useRef(false)
  useEffect(() => {
    function intercept(event: MouseEvent) {
      if (approved.current) { approved.current = false; return }
      if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || !(event.target instanceof Element)) return
      const link = event.target.closest<HTMLAnchorElement>('a[href]')
      const cancel = event.target.closest<HTMLButtonElement>('button')
      const navigation = link && link.target !== '_blank' && link.hash !== '#main-content' && link.href !== window.location.href
      const cancellation = cancel?.textContent?.trim() === 'Cancel'
      if (!navigation && !cancellation) return
      const relevant = [...unsavedForms].filter(([form]) => navigation || (cancel && form.contains(cancel)))
      if (!relevant.some(([, state]) => state().dirty || state().busy)) return
      event.preventDefault()
      event.stopImmediatePropagation()
      // Saving fields remain mounted until the request resolves.
      if (relevant.some(([, state]) => state().busy)) return
      setDestination(link ?? cancel)
    }
    function beforeUnload(event: BeforeUnloadEvent) {
      if ([...unsavedForms.values()].some(state => state().dirty || state().busy)) {
        event.preventDefault()
        event.returnValue = ''
      }
    }
    document.addEventListener('click', intercept, true)
    window.addEventListener('beforeunload', beforeUnload)
    return () => {
      document.removeEventListener('click', intercept, true)
      window.removeEventListener('beforeunload', beforeUnload)
    }
  }, [])
  return destination && <Modal title="Discard unsaved changes?" onClose={() => setDestination(null)}>
    <p>Your changes have not been saved. Keep editing or discard them to continue.</p>
    <div className="actions">
      <button type="button" className="secondary" onClick={() => setDestination(null)}>Keep editing</button>
      <button type="button" className="danger" onClick={() => {
        const target = destination
        setDestination(null)
        approved.current = true
        target.click()
      }}>Discard changes</button>
    </div>
  </Modal>
}
