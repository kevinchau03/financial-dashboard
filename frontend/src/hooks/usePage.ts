import { useEffect } from 'react'
import useHash from './useHash'
import { parseHash } from '../routing'

export const pages = [
  { path: '#/', title: 'Home' },
  { path: '#/dashboard', title: 'Dashboard' },
  { path: '#/budget', title: 'Budget' },
  { path: '#/accounts', title: 'Accounts' },
  { path: '#/budget-wrapped', title: 'Your Budget Wrapped' },
] as const

export default function usePage() {
  const hash = useHash()
  const { path } = parseHash(hash)
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [hash])
  useEffect(() => {
    document.title = `${pages.find(page => page.path === path)?.title ?? 'Page not found'} | MyBudgetPro`
    document.getElementById('main-content')?.focus({ preventScroll: true })
  }, [path])
  return path
}
