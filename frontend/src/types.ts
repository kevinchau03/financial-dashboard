export type Goal = {
  id: number
  name: string
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
  payments: { id: number; amount: string; paid_on: string; due_date: string | null }[]
}


