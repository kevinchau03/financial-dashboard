import { pages } from '../hooks/usePage'
import type { ReactNode } from 'react'

type NavigationProps = {
  path: string
  collapsed: boolean
  onToggle: () => void
  accountPanel: ReactNode
}

export default function Navigation({ path, collapsed, onToggle, accountPanel }: NavigationProps) {
  const isHome = path === '#/'

  return <header className={isHome ? 'site-header' : `site-header site-sidebar${collapsed ? ' is-collapsed' : ''}`}>
    <div className="navigation-content">
    <a className="brand site-brand" href="#/" aria-label="MyBudgetPro home">MyBudgetPro</a>
    <nav className="page-navigation" aria-label="Main navigation">
      {pages.filter(page => page.path !== '#/' && (!isHome || page.path !== '#/budget/paycheques')).map(page => <a key={page.path} href={page.path} className={page.path === '#/budget/paycheques' ? 'navigation-subpage' : undefined} aria-current={path === page.path ? 'page' : undefined}>{page.title}</a>)}
    </nav>
    </div>
    {accountPanel}
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
