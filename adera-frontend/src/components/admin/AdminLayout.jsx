import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import LogoMark from '../LogoMark'
import SkipLink from '../SkipLink'
import ThemeToggle from '../ThemeToggle'
import { useAuth } from '../../auth/useAuth'
import '../ui/ui.css'
import '../risk/risk.css'
import './admin.css'

// "also" keeps a nav item highlighted on its detail pages
const NAV = [
  { to: '/admin', label: 'Dashboard', end: true },
  { to: '/admin/alerts', label: 'Alerts' },
  { to: '/admin/entities', label: 'Entities', also: '/admin/entity/' },
  { to: '/admin/cases', label: 'Cases' },
]

function sectionOf(pathname) {
  if (pathname.startsWith('/admin/alerts')) return 'Alerts'
  if (pathname.startsWith('/admin/cases')) return 'Cases'
  if (pathname.startsWith('/admin/entit')) return 'Entities'
  return 'Dashboard'
}

export default function AdminLayout() {
  const { pathname } = useLocation()
  const { user, signOut } = useAuth()

  return (
    <div className="op-shell">
      <SkipLink />
      <aside className="op-side" aria-label="Fraud operations menu">
        <div className="op-brand">
          <LogoMark size={28} />
          <span>Adera</span>
          <small>አደራ</small>
        </div>

        <nav className="op-nav" aria-label="Main">
          {NAV.map(({ to, label, end, also }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                isActive || (also && pathname.startsWith(also)) ? 'is-active' : ''
              }
            >
              <span className="op-nav-node" aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="op-side-foot">
          <div className="op-user">
            <strong>{user?.name}</strong>
            <button type="button" onClick={() => signOut()}>Sign out</button>
          </div>
          <Link to="/" className="op-foot-link">← Customer app</Link>
        </div>
      </aside>

      <div className="op-body">
        <header className="op-top">
          <span className="op-top-title">{sectionOf(pathname)}</span>
          <ThemeToggle />
        </header>
        <main id="main" tabIndex={-1} className="op-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}