import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import CustomerShell from '../components/customer/CustomerShell'
import LogoMark from '../components/LogoMark'
import Button from '../components/ui/Button'
import Field from '../components/ui/Field'
import { homeFor } from '../auth/access'
import { useAuth } from '../auth/useAuth'
import { register, statusOf } from '../services/api'

const PHONE_RE = /^0[79]\d{8}$/ // 10 digits starting with 09 or 07

export default function Register() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [phone, setPhone] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={homeFor(user.role)} replace />

  async function handleSubmit(e) {
    e.preventDefault()
    if (busy) return
    if (!PHONE_RE.test(phone)) {
      setError('Enter a 10-digit phone number starting with 09 or 07.')
      return
    }
    if (name.trim().length < 2) {
      setError('Enter your full name.')
      return
    }
    if (password.length < 8) {
      setError('Use a password with at least 8 characters.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await register({ phone, name: name.trim(), password })
      navigate('/login', { replace: true, state: { notice: 'registered' } })
    } catch (err) {
      setBusy(false)
      setError(
        statusOf(err) === 409
          ? 'An account with this phone number already exists. Sign in instead.'
          : 'Could not create the account. Check your connection and try again.',
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
        <div className="cu-fields">
          <Field
            label="Phone number"
            mono
            name="phone"
            inputMode="numeric"
            autoComplete="tel"
            placeholder="09XXXXXXXX"
            value={phone}
            onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
          />
          <Field
            label="Full name"
            name="name"
            autoComplete="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Field
            label="Password"
            type="password"
            name="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && <p className="cu-error" role="alert">{error}</p>}

        <Button type="submit" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</Button>
        <Button variant="tertiary" onClick={() => navigate('/login')}>
          Already have an account? Sign in
        </Button>
      </form>
    </CustomerShell>
  )
}
