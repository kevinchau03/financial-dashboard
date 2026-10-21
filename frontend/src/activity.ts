import { parseHash } from './routing.ts'
import type { Payment } from './types.ts'

export type ActivityPage = {
  items: Payment[]
  total: number
  page: number
  page_size: number
  pages: number
}

export function activityFilters(hash: string) {
  const { params } = parseHash(hash)
  const kind = params.get('kind')
  const rawPage = params.get('page') ?? '1'
  return {
    kind: kind === 'bill' || kind === 'debt' || kind === 'goal' ? kind : 'all',
    page: /^[1-9]\d*$/.test(rawPage) && Number(rawPage) <= 1000000 ? Number(rawPage) : 1,
  } as const
}

export function activityHref(kind: string, page = 1) {
  const params = new URLSearchParams()
  if (kind !== 'all') params.set('kind', kind)
  if (page > 1) params.set('page', String(page))
  return `#/activity${params.size ? `?${params}` : ''}`
}

// Payment dates are calendar dates, not UTC instants.
export function paymentDate(value: string) {
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}
