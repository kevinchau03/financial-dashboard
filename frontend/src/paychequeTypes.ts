export type Allocation = {
  goal_id: number | null; debt_id: number | null; account_id: number | null
  id: number; kind: 'goal' | 'debt' | 'account'; name: string; amount: string
  status: 'planned' | 'completed' | 'cancelled'; completed_on: string | null
}
export type PaychequeRecord = {
  id: number; amount: string; received_on: string | null
  bills_reserved: string; spending_reserved: string; next_payday: string | null
  allocated_amount: string; remaining_amount: string; allocations: Allocation[]
}
