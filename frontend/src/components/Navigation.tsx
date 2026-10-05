import { pages } from '../hooks/usePage'

export default function Navigation({ path }: { path: string }) {
  return <header className={path === '#/' ? 'site-header' : 'site-header site-sidebar'}>
    <a className="brand site-brand" href="#/" aria-label="MyBudgetPro home">MyBudgetPro</a>
    <nav className="page-navigation" aria-label="Main navigation">
      {pages.filter(page => page.path !== '#/').map(page => <a key={page.path} href={page.path} aria-current={path === page.path ? 'page' : undefined}>{page.title}</a>)}
    </nav>
  </header>
}
