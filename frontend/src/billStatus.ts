import type { Bill } from './types'

export function billStatus(bill: Bill, today: string): 'paid' | 'unpaid' | 'overdue' {
  if (!bill.recurring) {
    if (bill.is_paid) return 'paid'
    return bill.due_date && bill.due_date < today ? 'overdue' : 'unpaid'
  }
  if (!bill.due_date) return bill.is_paid ? 'paid' : 'unpaid'
  if (bill.due_date < today) return 'overdue'
  if (bill.due_date === today) return 'unpaid'
  const previousOccurrencePaid = bill.payments.some(payment => payment.due_date !== null && payment.due_date < bill.due_date!)
  return bill.is_paid || previousOccurrencePaid ? 'paid' : 'unpaid'
}
