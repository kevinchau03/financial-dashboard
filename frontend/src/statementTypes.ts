export type SavedStatement = {
  statement_id: number; filename: string; imported_at: string; row_count: number
  start_date: string | null; end_date: string | null; has_file: boolean
}
export type StatementContents = {
  filename: string; headers: string[]; rows: (string | null)[][]; row_count: number
  statement_id: number; has_file: boolean
  stats: { total_income: string; total_spent: string; start_date: string | null; end_date: string | null }
}
export function statementDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}
