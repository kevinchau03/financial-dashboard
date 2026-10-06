export type Allocation = {
  id: number; kind: 'goal' | 'debt'; name: string; amount: string
  status: 'planned' | 'completed' | 'cancelled'; completed_on: string | null
}
export type PaychequeRecord = {
  id: number; amount: string; received_on: string | null
  allocated_amount: string; remaining_amount: string; allocations: Allocation[]
}
