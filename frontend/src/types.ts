export type CardTone = 'sky' | 'leaf' | 'sun' | 'rose'

export type PaymentKind = 'bill' | 'debt' | 'goal'
export type Payment = {
  id: number
  kind: PaymentKind
  target_id: number | null
  target_name: string
  amount: string
  paid_on: string
  due_date: string | null
  source: 'manual' | 'paycheque' | 'legacy'
  recorded_at: string | null
}

export type Goal = {
  id: number
  name: string
  account_id: number | null
  account_name: string | null
  target_amount: string
  current_amount: string
  due_date: string | null
  description: string | null
}

export type Bill = {
  id: number
  name: string
  amount: string
  due_date: string | null
  recurring: boolean
  description: string | null
  is_paid: boolean
  payments: Payment[]
}

export type Debt = {
  id: number
  name: string
  amount: string
  current_amount: string
  remaining_amount: string
  interest_rate: string | null
  due_date: string | null
  description: string | null
  is_paid: boolean
  payments: Payment[]
}
