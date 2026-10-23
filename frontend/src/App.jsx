import { useEffect, useState } from 'react'
import { BrowserRouter, Link, Navigate, Outlet, Route, Routes, useNavigate, useOutletContext } from 'react-router-dom'
import { api } from './services/api'
import UserPage from './pages/UserPage'
import AdminPage from './pages/AdminPage'
import AnalystLoginPage from './pages/AnalystLoginPage'
import './App.css'

const INTRO_SESSION_KEY = 'adera_intro_seen'



function markIntroSeen() {
  try {
    sessionStorage.setItem(INTRO_SESSION_KEY, '1')
  } catch {
    // Storage can be blocked; the intro is still allowed to finish this load.
  }
}

function LoginPage({ onAuthenticated }) {
  const navigate = useNavigate()
  const [registering, setRegistering] = useState(false)
  const [form, setForm] = useState({ phone: '', name: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (registering) {
        await api.register({ phone: form.phone, name: form.name, password: form.password })
      }

      const session = await api.login({ phone: form.phone, password: form.password })

      if (session.user?.role !== 'USER') {
        setError('This is an analyst or admin account. Please sign in through the Analyst Portal.')
        return
      }

      onAuthenticated(session)
      navigate('/user', { replace: true })
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <img className="brand-symbol brand-auth" src="/adera-mark.svg" alt="Adera" />
        <p className="eyebrow">ADERA · SAFE TRANSFERS</p>
        <h1>{registering ? 'Create your account' : 'Welcome back'}</h1>
        <p className="muted">Check recipient risk before money moves.</p>
        <form className="form-stack" onSubmit={submit}>
          {registering && <label>Full name<input required minLength="2" maxLength="100" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>}
          <label>Mobile number<input required minLength="7" maxLength="20" autoComplete="tel" placeholder="09…" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></label>
          <label>Password<input required minLength={registering ? 8 : undefined} type="password" autoComplete={registering ? 'new-password' : 'current-password'} value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary button-wide" disabled={busy}>{busy ? 'Please wait…' : registering ? 'Create account' : 'Sign in'}</button>
        </form>
        <p className="auth-toggle">{registering ? 'Already registered?' : 'New to Adera?'} <button className="text-button" onClick={() => { setRegistering(!registering); setError('') }}>{registering ? 'Sign in' : 'Create an account'}</button></p>
        <p className="small-note">Analyst workspaces require an account with an analyst or admin role assigned by the backend.</p>
      </section>
    </main>
  )
}

function Protected({ user, loading, roles }) {
  if (loading) return <main className="loading-screen">Loading your secure workspace…</main>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/user" replace />
  return <Outlet context={{ user }} />
}

function Workspace({ user, onLogout }) {
  const analyst = user.role === 'ANALYST' || user.role === 'ADMIN'
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="wordmark" to={analyst ? '/analyst' : '/user'}><img className="brand-symbol brand-small" src="/adera-mark.svg" alt="" /><span>Adera<span className="wordmark-sub"> · Safer mobile money</span></span></Link>
        <nav className="main-nav">
          {analyst ? <Link to="/analyst">Investigation desk</Link> : <><Link to="/user">Risk check</Link><Link to="/user/report">Report a scam</Link></>}
        </nav>
        <div className="account-chip"><span className="avatar">{user.name?.charAt(0)?.toUpperCase() || 'A'}</span><span className="account-name">{user.name}<small>{user.role}</small></span><button className="button button-quiet" onClick={onLogout}>Sign out</button></div>
      </header>
      <div className="workspace"><Outlet context={{ user }} /></div>
      <footer className="app-footer"><span>ADERA · Trust before transfer</span><span>Risk results are decision support, not a guarantee.</span></footer>
    </div>
  )
}

function WorkspaceLayout({ onLogout }) {
  const { user } = useOutletContext()
  return <Workspace user={user} onLogout={onLogout} />
}

function AppRoutes() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(api.getToken()))

  useEffect(() => {
    const handleUnauthorized = () => setUser(null)
    window.addEventListener('adera:unauthorized', handleUnauthorized)
    if (!api.getToken()) return () => window.removeEventListener('adera:unauthorized', handleUnauthorized)
    api.me().then(setUser).catch(() => { api.logout(); setUser(null) }).finally(() => setLoading(false))
    return () => window.removeEventListener('adera:unauthorized', handleUnauthorized)
  }, [])

  function authenticate(session) {
    api.setToken(session.access_token)
    setUser(session.user)
  }

  function logout() {
  const wasAnalyst = ['ANALYST', 'ADMIN'].includes(user?.role)

  api.logout()
  setUser(null)

  window.location.replace(wasAnalyst ? '/analyst-login' : '/login')
}
  const analystRoles = ['ANALYST', 'ADMIN']
  return (
    <Routes>
      <Route
    path="/analyst-login"
    element={
        user ? (
            <Navigate
                to={analystRoles.includes(user.role) ? '/analyst' : '/user'}
                replace
            />
        ) : (
            <AnalystLoginPage onAuthenticated={authenticate} />
        )
    }
/>
      <Route path="/login" element={user ? <Navigate to={user.role === 'USER' ? '/user' : '/analyst'} replace /> : <LoginPage onAuthenticated={authenticate} />} />
      <Route element={<Protected user={user} loading={loading} />}>
        <Route element={<WorkspaceLayout onLogout={logout} />}>
          <Route path="/user" element={<UserPage />} />
          <Route path="/user/report" element={<UserPage initialView="report" />} />
        </Route>
      </Route>
      <Route element={<Protected user={user} loading={loading} roles={analystRoles} />}>
        <Route element={<WorkspaceLayout onLogout={logout} />}>
          <Route path="/analyst" element={<AdminPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to={user ? (analystRoles.includes(user.role) ? '/analyst' : '/user') : '/login'} replace />} />
    </Routes>
  )
}

export default function App() {
  const [intro, setIntro] = useState('visible')

  useEffect(() => {
    if (intro === 'hidden') return undefined
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const delay = reducedMotion ? 0 : (intro === 'visible' ? 4600 : 700)
    const timer = window.setTimeout(
      () => {
        if (intro === 'visible') {
          markIntroSeen()
          setIntro(reducedMotion ? 'hidden' : 'leaving')
        } else {
          setIntro('hidden')
        }
      },
      delay,
    )
    return () => window.clearTimeout(timer)
  }, [intro])

  return <>
    <BrowserRouter><AppRoutes /></BrowserRouter>
    {intro !== 'hidden' && <div className={`brand-intro${intro === 'leaving' ? ' brand-intro-leaving' : ''}`} aria-label="Adera, for a safer digital Ethiopia">
      <div className="brand-intro-content">
        <div className="brand-intro-emblem" aria-hidden="true">
          <img src="/adera-mark.svg" alt="" />
        </div>
        <div className="brand-intro-copy">
          <p className="brand-intro-overline">ETHIOPIA · DIGITAL TRUST</p>
          <h1 className="brand-intro-wordmark">ADERA</h1>
          <span className="brand-intro-rule" aria-hidden="true"></span>
          <p className="brand-intro-tagline">FOR A SAFER DIGITAL ETHIOPIA</p>
        </div>
      </div>
    </div>}
  </>
}
