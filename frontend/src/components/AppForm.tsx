import { useEffect, useId, useRef, useState } from 'react'
import type { ComponentProps, SubmitEvent } from 'react'
import { formSnapshot, unsavedForms } from '../unsavedForms'

// Own constraint feedback while retaining native input types and keyboards.
export default function AppForm({ onSubmit, children, ...props }: ComponentProps<'form'>) {
  const id = useId()
  const pending = useRef(false)
  const formRef = useRef<HTMLFormElement>(null)
  useEffect(() => {
    const form = formRef.current!
    const initial = formSnapshot(form)
    unsavedForms.set(form, () => ({ dirty: formSnapshot(form) !== initial, busy: pending.current }))
    return () => { unsavedForms.delete(form) }
  }, [])
  const [errors, setErrors] = useState<{ name: string; message: string }[]>([])
  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending.current) return
    const form = event.currentTarget
    const fields = Array.from(form.elements).filter((field): field is HTMLInputElement | HTMLTextAreaElement => field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement)
    const recurring = fields.find(field => field.name === 'recurring') as HTMLInputElement | undefined
    const invalid = fields.flatMap((field, index) => {
      const blank = field.required && !field.value.trim()
      const missingDate = field.name === 'due_date' && recurring?.checked && !field.value
      const hint = missingDate ? 'Choose a due date for this monthly bill.' : blank ? 'Please fill in this field.' : !field.validity.valid ? field.validationMessage : ''
      const label = field.labels?.[0]?.textContent?.trim().split('\n')[0]
      const message = hint ? `${label ? `${label}: ` : ''}${hint}` : ''
      const errorId = `${id}-error-${index}`
      field.setAttribute('aria-invalid', String(Boolean(message)))
      if (message) field.setAttribute('aria-describedby', errorId)
      else if (field.getAttribute('aria-describedby')?.startsWith(id)) field.removeAttribute('aria-describedby')
      return message ? [{ name: errorId, message, field }] : []
    })
    setErrors(invalid)
    if (invalid.length) { invalid[0].field.focus(); return }
    pending.current = true
    try { await onSubmit?.(event) } finally { pending.current = false }
  }
  return <form {...props} ref={formRef} noValidate onSubmit={submit} onInput={event => {
    props.onInput?.(event)
    const field = event.target
    if ((field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement) && field.validity.valid && (!field.required || field.value.trim())) {
      const errorId = field.getAttribute('aria-describedby')
      if (errorId?.startsWith(id)) {
        field.removeAttribute('aria-describedby')
        field.setAttribute('aria-invalid', 'false')
        setErrors(previous => previous.filter(error => error.name !== errorId))
      }
    }
  }}>
    {children}
    {errors.length > 0 && <div className="form-errors" role="alert">{errors.map(error => <p id={error.name} key={error.name}>{error.message}</p>)}</div>}
  </form>
}

