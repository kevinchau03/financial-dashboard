import type { Bill } from './types'

export function sumAmounts(values: string[]) {
  return String(values.reduce((total, value) => total + Math.round(Number(value) * 100), 0) / 100)
}

export function upcomingBills(bills: Bill[]) {
  return bills.filter(bill => bill.recurring || !bill.is_paid).sort((first, second) =>
    (first.due_date ?? '9999-12-31').localeCompare(second.due_date ?? '9999-12-31') || first.id - second.id)
}
