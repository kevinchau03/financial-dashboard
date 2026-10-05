import { useEffect, useState } from 'react'

export const pages = [
  { path: '#/', title: 'Home' },
  { path: '#/budget', title: 'Budget' },
  { path: '#/accounts', title: 'Accounts' },
  { path: '#/budget-wrapped', title: 'Your Budget Wrapped' },
] as const

export default function usePage() {
  const [path, setPath] = useState(() => window.location.hash || '#/')
  useEffect(() => {
    const navigate = () => { setPath(window.location.hash || '#/'); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', navigate)
    return () => window.removeEventListener('hashchange', navigate)
  }, [])
  useEffect(() => {
    document.title = `${pages.find(page => page.path === path)?.title ?? 'Page not found'} | MyBudgetPro`
    document.getElementById('main-content')?.focus({ preventScroll: true })
  }, [path])
  return path
}
