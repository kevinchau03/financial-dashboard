import { apiFetch } from '../auth'
import { useEffect, useState } from 'react'

export default function useDashboardResource<T>(url: string, failureMessage = 'Unable to load this overview. Check your connection and retry.') {
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState<{ url: string; attempt: number; data: T | null; error: string } | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const response = await apiFetch(url, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]) })
        if (!response.ok) throw new Error(failureMessage)
        const data: T = await response.json()
        if (!controller.signal.aborted) setResult({ url, attempt, data, error: '' })
      } catch {
        if (!controller.signal.aborted) setResult({ url, attempt, data: null, error: failureMessage })
      }
    }
    void load()
    return () => controller.abort()
  }, [url, attempt, failureMessage])
  const current = result?.url === url && result.attempt === attempt ? result : null
  return { data: current?.data ?? null, loading: current === null, error: current?.error ?? '', retry: () => setAttempt(value => value + 1) }
}
