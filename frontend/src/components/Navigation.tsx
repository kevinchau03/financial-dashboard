import { pages } from '../hooks/usePage'

type NavigationProps = {
  path: string
  collapsed: boolean
  onToggle: () => void
}

export default function Navigation({ path, collapsed, onToggle }: NavigationProps) {
  const isHome = path === '#/'

  return <header className={isHome ? 'site-header' : `site-header site-sidebar${collapsed ? ' is-collapsed' : ''}`}>
    <a className="brand site-brand" href="#/" aria-label="MyBudgetPro home">MyBudgetPro</a>
    <nav className="page-navigation" aria-label="Main navigation">
      {pages.filter(page => page.path !== '#/').map(page => <a key={page.path} href={page.path} aria-current={path === page.path ? 'page' : undefined}>{page.title}</a>)}
    </nav>
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
