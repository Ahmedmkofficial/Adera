import { useCallback, useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import CustomerShell from '../components/customer/CustomerShell'
import LogoMark from '../components/LogoMark'
import Button from '../components/ui/Button'
import Field from '../components/ui/Field'
import { destinationFor } from '../auth/access'
import { INTRO_SESSION_KEY, SIGN_OUT_NOTICES } from '../auth/constants'
import { checkIdentifier, normalizeIdentifier, PHONE_RE } from '../auth/identifier'
import { useAuth } from '../auth/useAuth'
import { statusOf } from '../services/api'

export default function Login({ analyst = false }) {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, notice: endedBecause, signIn } = useAuth()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [showIntro, setShowIntro] = useState(
    () => !user && !hasPlayedIntro() && !prefersReducedMotion(),
  )

  const expectedRole = analyst ? 'analyst' : 'customer'

  const finishIntro = useCallback(() => setShowIntro(false), [])

  useEffect(() => {
    if (!user && !showIntro) rememberIntro()
  }, [user, showIntro])

  useEffect(() => {
    if (!showIntro) return undefined
    rememberIntro()
    const timeout = window.setTimeout(finishIntro, 2600)
    return () => window.clearTimeout(timeout)
  }, [showIntro, finishIntro])

  if (user?.role === expectedRole) {
    return <Navigate to={destinationFor(user.role, location.state?.from)} replace />
  }
  if (user) return <Navigate to="/" replace />

  const notice = SIGN_OUT_NOTICES[endedBecause ?? location.state?.notice]

  async function handleSubmit(e) {
    e.preventDefault()
    if (busy) return
    const problem = analyst
      ? checkIdentifier(identifier)
      : PHONE_RE.test(identifier.trim())
        ? ''
        : 'Enter a 10-digit phone number starting with 09 or 07.'
    if (problem) {
      setError(problem)
      return
    }
    if (!password) {
      setError('Enter your password.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await signIn(normalizeIdentifier(identifier), password, expectedRole)
    } catch (err) {
      setBusy(false)
      if (err?.code === 'ROLE_MISMATCH') {
        setError(
          analyst
            ? 'This account is for regular user access. Sign in with an analyst or admin account.'
            : 'This account is for analyst access. Use the analyst sign-in page.',
        )
      } else {
        setError(
          statusOf(err) === 401
            ? 'Those sign-in details are incorrect.'
            : 'Could not sign in. Check your connection and try again.',
        )
      }
    }
  }

  return (
    <CustomerShell
      mark={false}
      className={`cu-login-content${showIntro ? ' cu-login-logo-animating' : ''}`}
    >
      <div className="cu-wordmark">
        <LogoMark className="cu-wordmark-mark" size={60} animated={showIntro} />
        <h1 className="cu-wordmark-latin">Adera</h1>
        <div className="cu-wordmark-ethiopic">አደራ</div>
      </div>

      <form
        className="cu-form cu-login-form"
        onSubmit={handleSubmit}
        noValidate
        inert={showIntro}
      >
        {analyst && <p className="cu-login-kicker">ANALYST ACCESS</p>}
        <h2 className="cu-login-title">{analyst ? 'Analyst sign in' : 'Welcome back'}</h2>
        {notice && <p className="cu-notice cu-notice-top" role="status">{notice}</p>}

        <div className="cu-fields">
          <Field
            label={analyst ? 'Staff username or phone number' : 'Phone number'}
            mono
            name="username"
            autoComplete="username"
            autoCapitalize="none"
            spellCheck={false}
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value.replace(/\s/g, '').slice(0, 32))}
          />
          <Field
            label="Password"
            type="password"
            name="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && <p className="cu-error" role="alert">{error}</p>}

        <Button type="submit" disabled={busy} aria-busy={busy}>
          {busy ? 'Signing in…' : analyst ? 'Sign in to analyst dashboard' : 'Sign in'}
        </Button>
        {analyst ? (
          <Link className="ad-btn ad-btn-tertiary cu-login-link" to="/login">
            User sign in
          </Link>
        ) : (
          <>
            <Button variant="tertiary" onClick={() => navigate('/register')}>
              Create account
            </Button>
            <Link className="cu-login-staff-link" to="/analyst/login">
              Analyst or admin? Sign in here
            </Link>
          </>
        )}
      </form>
    </CustomerShell>
  )
}

function hasPlayedIntro() {
  try {
    return sessionStorage.getItem(INTRO_SESSION_KEY) === 'true'
  } catch {
    return false
  }
}

function rememberIntro() {
  try {
    sessionStorage.setItem(INTRO_SESSION_KEY, 'true')
  } catch {
    // Intro timing still completes if session storage is unavailable.
  }
}

function prefersReducedMotion() {
  return typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
}
