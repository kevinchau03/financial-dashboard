// Older running APIs may not yet include the occurrence count.
export function transactionOccurrences(name: string | null, count: number | undefined, rows: readonly (readonly (string | null)[])[]): number {
  if (name === null) return 0
  if (typeof count === 'number' && Number.isSafeInteger(count) && count > 0) return count
  return rows.filter(row => row[1] === name).length
}
