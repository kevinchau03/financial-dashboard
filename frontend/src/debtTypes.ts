import type { DebtKind, DebtPaymentFrequency } from './types'

export const debtTypes: Record<DebtKind, string> = {
  credit_card: 'Credit card',
  line_of_credit: 'Line of credit',
  personal_loan: 'Personal loan',
  auto_loan: 'Auto loan',
  student_loan: 'Student loan',
  mortgage: 'Mortgage',
  buy_now_pay_later: 'Buy now, pay later',
  personal_debt: 'Personal debt',
}

export const paymentFrequencies: Record<DebtPaymentFrequency, string> = {
  weekly: 'Weekly',
  biweekly: 'Every two weeks',
  semimonthly: 'Twice a month',
  monthly: 'Monthly',
  quarterly: 'Every three months',
  annually: 'Annually',
}

export const isRevolvingDebt = (type: DebtKind) => type === 'credit_card' || type === 'line_of_credit'
