import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import CustomerShell from '../components/customer/CustomerShell'
import LogoMark from '../components/LogoMark'
import Button from '../components/ui/Button'
import Field from '../components/ui/Field'
import { destinationFor } from '../auth/access'
import { SIGN_OUT_NOTICES } from '../auth/constants'
import { checkIdentifier, normalizeIdentifier } from '../auth/identifier'
import { useAuth } from '../auth/useAuth'
import { statusOf } from '../services/api'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, notice: endedBecause, signIn } = useAuth()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // Already signed in (or just signed in): go where this role belongs.
  if (user) return <Navigate to={destinationFor(user.role, location.state?.from)} replace />

  const notice = SIGN_OUT_NOTICES[endedBecause ?? location.state?.notice]

  async function handleSubmit(e) {
    e.preventDefault()
    if (busy) return
    const problem = checkIdentifier(identifier)
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
      await signIn(normalizeIdentifier(identifier), password) // on success this page redirects by itself
    } catch (err) {
      setBusy(false)
      // The same message for a wrong name or a wrong password, on purpose.
      setError(
        statusOf(err) === 401
          ? 'Those sign-in details are incorrect.'
          : 'Could not sign in. Check your connection and try again.',
      )
    }
  }

  return (
    <CustomerShell mark={false}>
      <div className="cu-wordmark">
        <LogoMark className="cu-wordmark-mark" size={60} />
        <h1 className="cu-wordmark-latin">Adera</h1>
        <div className="cu-wordmark-ethiopic">አደራ</div>
      </div>

      <form className="cu-form" onSubmit={handleSubmit} noValidate>
        {notice && <p className="cu-notice cu-notice-top" role="status">{notice}</p>}

        <div className="cu-fields">
          <Field
            label="Phone number or username"
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

        <Button type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</Button>
        <Button variant="tertiary" onClick={() => navigate('/register')}>
          Create account
        </Button>
      </form>
    </CustomerShell>
  )
}
