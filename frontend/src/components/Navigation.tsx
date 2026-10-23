import { pages } from '../hooks/usePage'
import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'

type NavigationProps = {
  path: string
  collapsed: boolean
  onToggle: () => void
  accountPanel: ReactNode
}

export default function Navigation({ path, collapsed, onToggle, accountPanel }: NavigationProps) {
  const isHome = path === '#/'
  const [mobileOpen, setMobileOpen] = useState(false)
  const mobileToggle = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const close = () => setMobileOpen(false)
    const desktop = window.matchMedia('(min-width: 641px)')
    window.addEventListener('hashchange', close)
    desktop.addEventListener('change', close)
    return () => {
      window.removeEventListener('hashchange', close)
      desktop.removeEventListener('change', close)
    }
  }, [])

  return <header className={`${isHome ? 'site-header' : `site-header site-sidebar${collapsed ? ' is-collapsed' : ''}`}${mobileOpen ? ' mobile-navigation-open' : ''}`} onKeyDown={event => {
    if (event.key === 'Escape' && mobileOpen) {
      event.preventDefault()
      setMobileOpen(false)
      mobileToggle.current?.focus()
    }
  }}>
    <div className="navigation-content">
    <a className="brand site-brand" href="#/" aria-label="MyBudgetPro home">MyBudgetPro</a>
    <button ref={mobileToggle} className="mobile-navigation-toggle" type="button" aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={mobileOpen} aria-controls="primary-navigation navigation-account" onClick={() => setMobileOpen(open => !open)}>
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d={mobileOpen ? 'M6 6l12 12M6 18L18 6' : 'M4 6h16M4 12h16M4 18h16'} /></svg>
    </button>
    <nav id="primary-navigation" className="page-navigation" aria-label="Main navigation" onClick={event => {
      if (event.target instanceof Element && event.target.closest('a')) setMobileOpen(false)
    }}>
      {pages.filter(page => page.path !== '#/' && (!isHome || page.path !== '#/budget/paycheques')).map(page => <a key={page.path} href={page.path} className={page.path === '#/budget/paycheques' ? 'navigation-subpage' : undefined} aria-current={path === page.path ? 'page' : undefined}>{page.title}</a>)}
    </nav>
    </div>
    <div id="navigation-account" className="navigation-account">{accountPanel}</div>
    {!isHome && <button
      className="sidebar-toggle"
      type="button"
      aria-label={collapsed ? 'Open navigation' : 'Close navigation'}
      aria-expanded={!collapsed}
      onClick={onToggle}
    >
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="m10 3-5 5 5 5" />
      </svg>
    </button>}
  </header>
}
