import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Segmented from '../components/ui/Segmented'
import RiskMark from '../components/admin/RiskMark'
import { getCases } from '../services/api'
import { DECISION_LABEL, STATUS_LABEL, formatCaseId, timeAgo } from '../utils/format'
import { levelClass } from '../utils/risk'
import '../components/admin/case.css'

const FILTERS = ['All', 'Open', 'Closed']

export default function CaseListPage() {
  const [cases, setCases] = useState(null)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('All')

  useEffect(() => {
    let cancelled = false
    getCases()
      .then((data) => {
        if (!cancelled) setCases(data)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the cases. Please refresh the page.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const rows = (cases ?? []).filter((c) => filter === 'All' || STATUS_LABEL[c.status] === filter)

  return (
    <div className="op-page">
      <div className="op-heading">
        <div>
          <p className="op-eyebrow">FRAUD OPERATIONS</p>
          <h1>Cases</h1>
        </div>
        <Segmented items={FILTERS} value={filter} onChange={setFilter} label="Filter by status" />
      </div>

      {error && <p className="op-error" role="alert">{error}</p>}
      {!error && !cases && <p className="op-empty">Loading cases…</p>}

      {cases && (
        <>
          <div className="op-table-meta">
            <span>{rows.length} {rows.length === 1 ? 'case' : 'cases'}</span>
          </div>

          <div className="op-table">
            <div className="op-row cs-row op-row-head">
              <span>Case</span>
              <span>Status</span>
              <span>Subject</span>
              <span>Risk</span>
              <span>Last decision</span>
              <span>Updated</span>
            </div>

            {rows.map((c) => (
              <Link key={c.id} to={`/admin/cases/${c.id}`} className="op-row cs-row">
                <span className="mono">{formatCaseId(c.id)}</span>
                <span className={`op-status op-status-${c.status.toLowerCase()}`}>
                  <i aria-hidden="true" />
                  {STATUS_LABEL[c.status]}
                </span>
                <span className="mono">{c.subject}</span>
                {c.score != null && c.level ? (
                  <span className="op-score-cell">
                    <strong className={`op-score ${levelClass(c.level)}`}>{c.score}</strong>
                    <RiskMark score={c.score} level={c.level} />
                  </span>
                ) : (
                  <span className="op-muted">Risk unavailable</span>
                )}
                <span>{c.decision ? DECISION_LABEL[c.decision] : '—'}</span>
                <span className="op-muted">{timeAgo(c.updated_at)}</span>
              </Link>
            ))}

            {rows.length === 0 && <p className="op-empty">No cases here yet.</p>}
          </div>
        </>
      )}
    </div>
  )
}