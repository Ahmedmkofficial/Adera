import { useEffect, useRef } from 'react'
import { matchPath, useLocation } from 'react-router-dom'

// [address pattern, page title]
const TITLES = [
  ['/login', () => 'Sign in'],
  ['/register', () => 'Create account'],
  ['/', () => 'Send money'],
  ['/report', () => 'Report'],
  ['/confirmation/:type', () => 'Receipt'],
  ['/admin', () => 'Overview'],
  ['/admin/alerts', () => 'Alerts'],
  ['/admin/alerts/:id', (p) => `Alert #${p.id}`],
  ['/admin/entities', () => 'Entities'],
  ['/admin/entity/:phone', (p) => `Entity ${p.phone}`],
  ['/admin/entity/:phone/graph', (p) => `Graph ${p.phone}`],
  ['/admin/cases', () => 'Cases'],
  ['/admin/cases/:id', (p) => `Case #${p.id}`],
]

function titleFor(pathname) {
  for (const [pattern, title] of TITLES) {
    const match = matchPath({ path: pattern, end: true }, pathname)
    if (match) return title(match.params)
  }
  return null
}

// Runs on every page change: sets the browser tab title, scrolls to the top and
// moves keyboard focus to the page content so screen readers announce the change.
export default function RouteEffects() {
  const { pathname } = useLocation()
  const first = useRef(true)

  useEffect(() => {
    const title = titleFor(pathname)
    document.title = title ? `${title} · Adera` : 'Adera'
    if (first.current) {
      first.current = false
      return
    }
    window.scrollTo(0, 0)
    document.getElementById('main')?.focus({ preventScroll: true })
  }, [pathname])

  return null
}
