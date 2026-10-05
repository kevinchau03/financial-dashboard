export function cents(value: string): number {
  return Math.round(Number(value) * 100)
}

export function savingsPlan(target: string, saved: string, due: string | null, today: string) {
  const remaining = Math.max(0, cents(target) - cents(saved))
  if (!remaining) return { remaining, status: 'funded', months: 0, monthly: 0 }
  if (!due) return { remaining, status: 'flexible', months: 0, monthly: 0 }
  if (due < today) return { remaining, status: 'past-due', months: 0, monthly: 0 }
  // One contribution today, then monthly on this day (clamped in short months).
  const [year, month, day] = today.split('-').map(Number)
  const [dueYear, dueMonth, dueDay] = due.split('-').map(Number)
  const distance = (dueYear - year) * 12 + dueMonth - month
  const lastDay = new Date(Date.UTC(dueYear, dueMonth, 0)).getUTCDate()
  const months = Math.max(1, distance + (dueDay >= Math.min(day, lastDay) ? 1 : 0))
  return { remaining, status: 'planned', months, monthly: Math.ceil(remaining / months) }
}
