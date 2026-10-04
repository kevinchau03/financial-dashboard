import { useEffect, useState } from 'react'
import { amount } from '../api'
import StatCard from './StatCard'

type Metric = { title: string; endpoint: string; field: string; description: string }

const metrics: Metric[] = [
  { title: 'Total savings', endpoint: '/api/analytics/savings', field: 'total_savings', description: 'Saved across all your financial goals.' },
  { title: 'Remaining debt', endpoint: '/api/analytics/debts', field: 'total_debt', description: 'Total debt balance still to repay.' },
  { title: 'Total bills', endpoint: '/api/analytics/bills', field: 'total_bills', description: 'All recorded bill amounts, including paid bills.' },
]

function MetricCard({ metric, revision }: { metric: Metric; revision: number }) {
  const [value, setValue] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(metric.endpoint, { signal: controller.signal })
        if (!response.ok) throw new Error('Unable to load summary.')
        const data: Record<string, string> = await response.json()
        const total = data[metric.field]
        if (typeof total !== 'string' || !Number.isFinite(Number(total))) throw new Error('Invalid summary.')
        if (!controller.signal.aborted) setValue(total)
      } catch {
        if (!controller.signal.aborted) setError(`Unable to load ${metric.title.toLowerCase()}.`)
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    void load()
    return () => controller.abort()
  }, [metric, revision, attempt])

  return <StatCard title={metric.title} value={value === null ? '—' : amount(value)}
    description={metric.description} loading={loading} error={error}
    onRetry={() => setAttempt(previous => previous + 1)} />
}

export default function Analytics({ revision }: { revision: number }) {
  return <div className="analytics-cards">
    {metrics.map(metric => <MetricCard key={metric.field} metric={metric} revision={revision} />)}
  </div>
}
