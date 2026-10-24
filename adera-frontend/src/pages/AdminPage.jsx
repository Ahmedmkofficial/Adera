import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Segmented from '../components/ui/Segmented'
import RiskMark from '../components/admin/RiskMark'
import { getAlerts, getDashboardSummary } from '../services/api'
import { formatAlertId, timeAgo } from '../utils/format'
import { levelLabel } from '../utils/risk'

const FILTERS = ['All', 'Critical', 'High', 'Moderate']

export default function AdminPage() {
  const [now] = useState(() => new Date())
  const [summary, setSummary] = useState(null)
  const [alerts, setAlerts] = useState(null)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('All')

  useEffect(() => {
    let cancelled = false
    Promise.all([getDashboardSummary(), getAlerts()])
      .then(([s, a]) => {
        if (cancelled) return
        setSummary(s)
        setAlerts(a)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the dashboard. Please refresh the page.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const dateText = now
    .toLocaleDateString('en-GB', { day: 'numeric', month: 'long' })
    .toUpperCase()
  const timeText = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })

  const metrics = [
    [summary?.alerts, 'Alerts', ''],
    [summary?.critical, 'Critical', 'lvl-critical'],
    [summary?.high, 'High risk', ''],
    [summary?.open_cases, 'Open cases', ''],
    [summary?.reports, 'Reports', ''],
  ]

  const rows = (alerts ?? [])
    .filter((a) => filter === 'All' || levelLabel(a.level) === filter)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

  return (
    <div className="op-page">
      <div className="op-heading">
        <div>
          <p className="op-eyebrow">TODAY · {dateText}</p>
          <h1>Overview</h1>
        </div>
        <p className="op-heading-note">Updated {timeText}</p>
      </div>

      <section className="op-metrics" aria-label="Operations summary">
        {metrics.map(([value, label, tone]) => (
          <div className={`op-metric ${tone}`} key={label}>
            <strong>{value ?? '–'}</strong>
            <span>{label}</span>
          </div>
        ))}
      </section>

      <section>
        <div className="op-section-head">
          <div>
            <h2>Recent alerts</h2>
            <p>Incoming indicators requiring review</p>
          </div>
          <Segmented items={FILTERS} value={filter} onChange={setFilter} label="Filter by risk level" />
        </div>

        {error && <p className="op-error" role="alert">{error}</p>}
        {!error && !alerts && <p className="op-empty">Loading alerts…</p>}

        {alerts && (
          <div className="op-table">
            <div className="op-row op-row-head">
              <span>Alert</span>
              <span>Recipient</span>
              <span>Risk</span>
              <span>Primary indicator</span>
              <span>Received</span>
            </div>

            {rows.map((a) => (
              <Link key={a.id} to={`/admin/alerts/${a.id}`} className="op-row">
                <span className="mono">{formatAlertId(a.id)}</span>
                <span className="mono">{a.recipient_phone}</span>
                <RiskMark score={a.score} level={a.level} />
                <span>{a.reason}</span>
                <span className="op-muted">{timeAgo(a.created_at)}</span>
              </Link>
            ))}

            {rows.length === 0 && <p className="op-empty">No alerts at this level.</p>}
          </div>
        )}
      </section>
    </div>
  )
}