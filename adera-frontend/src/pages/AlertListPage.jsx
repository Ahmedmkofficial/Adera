import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import Segmented from '../components/ui/Segmented'
import RiskMark from '../components/admin/RiskMark'
import { getAlerts } from '../services/api'
import { STATUS_LABEL, formatAlertId, timeAgo } from '../utils/format'
import { levelLabel } from '../utils/risk'

const FILTERS = ['All levels', 'Critical', 'High', 'Moderate']

// sortable columns: how to read the value we sort by
const SORT_VALUE = {
  id: (a) => a.id,
  score: (a) => a.score,
  created: (a) => new Date(a.created_at).getTime(),
}

function SortButton({ label, sortKey, sort, onSort }) {
  const active = sort.key === sortKey
  const arrow = active ? (sort.dir === 'asc' ? '↑' : '↓') : '↕'
  const state = active
    ? `currently ${sort.dir === 'asc' ? 'ascending' : 'descending'}`
    : 'not sorted'
  return (
    <button
      type="button"
      className={`op-sort${active ? ' is-sorted' : ''}`}
      aria-label={`Sort by ${label}, ${state}`}
      onClick={() => onSort(sortKey)}
    >
      {label} <span aria-hidden="true">{arrow}</span>
    </button>
  )
}

export default function AlertListPage() {
  const [alerts, setAlerts] = useState(null)
  const [refreshedAt, setRefreshedAt] = useState(null)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('All levels')
  const [sort, setSort] = useState({ key: 'created', dir: 'desc' })

  useEffect(() => {
    let cancelled = false
    getAlerts()
      .then((data) => {
        if (cancelled) return
        setAlerts(data)
        setRefreshedAt(new Date())
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the alerts. Please refresh the page.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  function handleSort(key) {
    // same column again = flip direction; new column = start high-to-low
    setSort((prev) =>
      prev.key === key
        ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: 'desc' },
    )
  }

  const rows = useMemo(() => {
    const list = (alerts ?? []).filter(
      (a) => filter === 'All levels' || levelLabel(a.level) === filter,
    )
    const read = SORT_VALUE[sort.key]
    const sign = sort.dir === 'asc' ? 1 : -1
    return [...list].sort((a, b) => (read(a) - read(b)) * sign)
  }, [alerts, filter, sort])

  const refreshedText = refreshedAt?.toLocaleTimeString('en-GB')

  return (
    <div className="op-page">
      <div className="op-heading">
        <div>
          <p className="op-eyebrow">FRAUD OPERATIONS</p>
          <h1>Alerts</h1>
        </div>
        <Segmented items={FILTERS} value={filter} onChange={setFilter} label="Filter by risk level" />
      </div>

      {error && <p className="op-error" role="alert">{error}</p>}
      {!error && !alerts && <p className="op-empty">Loading alerts…</p>}

      {alerts && (
        <>
          <div className="op-table-meta">
            <span>{rows.length} {rows.length === 1 ? 'alert' : 'alerts'}</span>
            <span>
              Last refreshed <span className="mono">{refreshedText}</span>
            </span>
          </div>

          <div className="op-table">
            <div className="op-row op-row-full op-row-head">
              <SortButton label="Alert" sortKey="id" sort={sort} onSort={handleSort} />
              <span>Recipient</span>
              <SortButton label="Risk" sortKey="score" sort={sort} onSort={handleSort} />
              <span>Primary indicator</span>
              <span>Status</span>
              <SortButton label="Received" sortKey="created" sort={sort} onSort={handleSort} />
            </div>

            {rows.map((a) => (
              <Link key={a.id} to={`/admin/alerts/${a.id}`} className="op-row op-row-full">
                <span className="mono">{formatAlertId(a.id)}</span>
                <span className="mono">{a.recipient_phone}</span>
                <span className="op-score-cell">
                  <strong className={`op-score lvl-${a.level.toLowerCase()}`}>{a.score}</strong>
                  <RiskMark score={a.score} level={a.level} />
                </span>
                <span>{a.reason}</span>
                <span className={`op-status op-status-${a.status.toLowerCase()}`}>
                  <i aria-hidden="true" />
                  {STATUS_LABEL[a.status]}
                </span>
                <span className="op-muted">{timeAgo(a.created_at)}</span>
              </Link>
            ))}

            {rows.length === 0 && <p className="op-empty">No alerts at this level.</p>}
          </div>
        </>
      )}
    </div>
  )
}