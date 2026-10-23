import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Button from '../components/ui/Button'
import Field from '../components/ui/Field'
import RiskMark from '../components/admin/RiskMark'
import { getAlerts } from '../services/api'
import '../components/admin/entity.css'

const PHONE_RE = /^0[79]\d{8}$/ // 10 digits starting with 09 or 07

export default function EntitiesPage() {
  const navigate = useNavigate()
  const [phone, setPhone] = useState('')
  const [error, setError] = useState('')
  const [known, setKnown] = useState(null)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    let cancelled = false
    getAlerts()
      .then((alerts) => {
        if (cancelled) return
        // one row per phone number, highest risk first
        const byPhone = new Map()
        alerts.forEach((a) => byPhone.set(a.recipient_phone, a))
        setKnown([...byPhone.values()].sort((a, b) => b.score - a.score))
      })
      .catch(() => {
        if (!cancelled) setLoadError('Could not load the list. Please refresh the page.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  function handleSubmit(e) {
    e.preventDefault()
    if (!PHONE_RE.test(phone)) {
      setError('Enter a 10-digit phone number starting with 09 or 07.')
      return
    }
    setError('')
    navigate(`/admin/entity/${phone}`)
  }

  return (
    <div className="op-page">
      <div className="op-heading">
        <div>
          <p className="op-eyebrow">FRAUD OPERATIONS</p>
          <h1>Entities</h1>
        </div>
      </div>

      <form className="ent-search" onSubmit={handleSubmit} noValidate>
        <Field
          label="Look up a phone number"
          mono
          name="phone"
          inputMode="numeric"
          placeholder="09XXXXXXXX"
          value={phone}
          onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
        />
        {error && <p className="op-error" role="alert">{error}</p>}
        <Button type="submit">Open profile</Button>
      </form>

      <section>
        <div className="op-section-head">
          <div>
            <h2>Entities with alerts</h2>
            <p>Recipients that have raised at least one alert</p>
          </div>
        </div>

        {loadError && <p className="op-error" role="alert">{loadError}</p>}
        {!loadError && !known && <p className="op-empty">Loading entities…</p>}

        {known && (
          <div className="op-table">
            <div className="op-row ent-known-row op-row-head">
              <span>Recipient</span>
              <span>Risk</span>
              <span>Primary indicator</span>
            </div>
            {known.map((a) => (
              <Link
                key={a.recipient_phone}
                to={`/admin/entity/${a.recipient_phone}`}
                className="op-row ent-known-row"
              >
                <span className="mono">{a.recipient_phone}</span>
                <RiskMark score={a.score} level={a.level} />
                <span>{a.reason}</span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}