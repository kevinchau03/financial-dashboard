import { useCallback, useEffect, useRef, useState } from 'react'

export default function useNotice() {
  const [notice, setNotice] = useState('')
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showNotice = useCallback((message: string) => {
    if (timer.current !== null) clearTimeout(timer.current)
    setNotice(message)
    timer.current = message ? setTimeout(() => {
      setNotice('')
      timer.current = null
    }, 3000) : null
  }, [])

  useEffect(() => () => {
    if (timer.current !== null) clearTimeout(timer.current)
  }, [])

  return [notice, showNotice] as const
}
