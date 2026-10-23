import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../services/api'

export default function AnalystLoginPage({ onAuthenticated }) {
    const navigate = useNavigate()
    const [phone, setPhone] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)

    async function submit(event) {
        event.preventDefault()
        setError('')
        setBusy(true)

        try {
            const session = await api.login({ phone, password })

            if (!['ANALYST', 'ADMIN'].includes(session.user?.role)) {
                setError('This account is not authorized for the analyst portal.')
                return
            }

            onAuthenticated(session)
            navigate('/analyst', { replace: true })
        } catch (requestError) {
            setError(requestError.message)
        } finally {
            setBusy(false)
        }
    }

    return (
        <main className="analyst-login-shell">
            <section className="analyst-login-card">
                <Link to="/login" className="analyst-back-link">
                    ← Back to Adera
                </Link>

                <div className="analyst-brand">
                    <img src="/adera-mark.svg" alt="" />
                    <div>
                        <p className="analyst-eyebrow">ADERA SECURITY</p>
                        <h1>Investigation Desk</h1>
                    </div>
                </div>

                <div className="analyst-login-intro">
                    <span className="analyst-lock" aria-hidden="true">⌑</span>
                    <h2>Analyst sign in</h2>
                    <p>
                        Secure access to fraud alerts, investigations,
                        and recipient intelligence.
                    </p>
                </div>

                <form className="analyst-login-form" onSubmit={submit}>
                    <label htmlFor="analyst-phone">Staff account phone number</label>
                    <input
                        id="analyst-phone"
                        type="tel"
                        autoComplete="username"
                        placeholder="Enter your registered number"
                        minLength={7}
                        maxLength={20}
                        required
                        value={phone}
                        onChange={(event) => setPhone(event.target.value)}
                    />

                    <label htmlFor="analyst-password">Password</label>
                    <input
                        id="analyst-password"
                        type="password"
                        autoComplete="current-password"
                        required
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                    />

                    {error && <p className="analyst-login-error" role="alert">{error}</p>}

                    <button type="submit" disabled={busy}>
                        {busy ? 'Verifying credentials…' : 'Sign in securely'}
                    </button>
                </form>

                <p className="analyst-login-notice">
                    Authorized personnel only. Access permissions are verified
                    using your assigned account role.
                </p>
            </section>
        </main>
    )
}
