export function parseHash(hash: string) {
  const separator = hash.indexOf('?')
  const rawPath = separator < 0 ? hash : hash.slice(0, separator)
  const trimmedPath = rawPath.replace(/\/+$/, '')
  const path = !trimmedPath ? '#/dashboard' : trimmedPath === '#' ? '#/' : trimmedPath
  const params = new URLSearchParams(separator < 0 ? '' : hash.slice(separator + 1))
  return { path, params }
}

export function statementIdFromHash(hash: string): number | null {
  const value = parseHash(hash).params.get('statement')
  return value && /^[1-9]\d*$/.test(value) && Number.isSafeInteger(Number(value)) ? Number(value) : null
}
