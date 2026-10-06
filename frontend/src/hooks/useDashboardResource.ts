import { useEffect, useState } from 'react'

export default function useDashboardResource<T>(url: string) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await fetch(url, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]) })
        if (!response.ok) throw new Error('Unable to load this overview. Please retry.')
        const result: T = await response.json()
        if (!controller.signal.aborted) setData(result)
      } catch {
        if (!controller.signal.aborted) setError('Unable to load this overview. Check your connection and retry.')
      } finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load()
    return () => controller.abort()
  }, [url, attempt])
  return { data, loading, error, retry: () => { setLoading(true); setError(''); setAttempt(value => value + 1) } }
}
