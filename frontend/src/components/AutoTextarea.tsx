import type { ComponentProps } from 'react'

export default function AutoTextarea(props: ComponentProps<'textarea'>) {
  return <textarea {...props} className={`resize-none ${props.className ?? ''}`} style={{ ...props.style, resize: 'none', minHeight: 100 }} onInput={event => {
    event.currentTarget.style.height = 'auto'
    event.currentTarget.style.height = `${event.currentTarget.scrollHeight}px`
    props.onInput?.(event)
  }} />
}
