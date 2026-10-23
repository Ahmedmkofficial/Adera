import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Segmented from '../components/ui/Segmented'
import Thread from '../components/risk/Thread'
import TransactionList from '../components/admin/TransactionList'
import ReportList from '../components/admin/ReportList'
import RelatedAccounts from '../components/admin/RelatedAccounts'
import RiskChart from '../components/admin/RiskChart'
import useCountUp from '../utils/useCountUp'
import { getEntity } from '../services/api'
import { STATUS_LABEL, formatCaseId, formatDate, timeAgo } from '../utils/format'
import { RECOMMENDATION_LABEL, levelClass, levelLabel } from '../utils/risk'
import '../components/admin/entity.css'

const TABS = ['Overview', 'Transactions', 'Reports', 'Relationships', 'Risk history', 'Cases']

// A new phone number in the address starts the page fresh (key = phone)
export default function EntityRoute() {
  const { phone } = useParams()
  return <EntityPage key={phone} phone={phone} />
}

function ScoreBlock({ score, level }) {
  const shown = useCountUp(score)
  return (
    <div
      className={`ent-score ${levelClass(level)}`}
      role="img"
      aria-label={`Risk score ${score} out of 100, ${levelLabel(level)}`}
    >
      <strong>{shown}</strong>
      <span className="ent-of">/100</span>
      <div className="ent-level">{levelLabel(level)}</div>
    </div>
  )
}

function PanelHead({ title, note, aside }) {
  return (
    <div className="ent-panel-head">
      <div>
        <h2>{title}</h2>
        <p>{note}</p>
      </div>
      {aside}
    </div>
  )
}

function EntityPage({ phone }) {
  const [entity, setEntity] = useState(undefined) // undefined = loading, null = not found
  const [error, setError] = useState('')
  const [tab, setTab] = useState('Overview')

  useEffect(() => {
    let cancelled = false
    getEntity(phone)
      .then((data) => {
        if (!cancelled) setEntity(data)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load this profile. Please refresh the page.')
      })
    return () => {
      cancelled = true
    }
  }, [phone])

  if (error) {
    return (
      <div className="op-page">
        <p className="op-error" role="alert">{error}</p>
      </div>
    )
  }
  if (entity === undefined) {
    return (
      <div className="op-page">
        <p className="op-empty">Loading profile…</p>
      </div>
    )
  }
  if (entity === null) {
    return (
      <div className="op-page">
        <h1 className="iv-notfound">No record found</h1>
        <p className="op-muted">
          Adera has no intelligence on {phone}. <Link to="/admin/entities">Back to entities</Link>
        </p>
      </div>
    )
  }

  const e = entity
  const stats = [
    [e.reports_count, 'Reports'],
    [e.recent_reports, 'Recent'],
    [e.scam_cases, 'Scam cases'],
    [
      e.related_accounts_count ?? e.suspicious_relationship_count,
      e.related_accounts_count == null ? 'Suspicious relationships' : 'Related accounts',
    ],
  ]

  return (
    <div className="op-page">
      <div className="ent-head">
        <div>
          <p className="op-eyebrow">RECIPIENT</p>
          <h1 className="ent-phone mono">{e.phone}</h1>
          {(e.first_observed || e.last_activity) && (
            <p className="ent-meta">
              {e.first_observed && <>First observed {formatDate(e.first_observed)}</>}
              {e.first_observed && e.last_activity && ' · '}
              {e.last_activity && <>Last activity {timeAgo(e.last_activity)}</>}
            </p>
          )}
        </div>
        <ScoreBlock score={e.score} level={e.level} />
      </div>

      <section className="op-metrics ent-stats" aria-label="Entity summary">
        {stats.map(([value, label]) => (
          <div className="op-metric" key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </section>

      <div className="ent-tabs">
        <Segmented items={TABS} value={tab} onChange={setTab} label="Profile section" />
      </div>

      <div className="ent-panel">
        {tab === 'Overview' && (
          <>
            <PanelHead title="Risk indicators" note="What contributes to the current score" />
            {e.reasons?.length > 0 ? (
              <Thread items={e.reasons} level={e.level} />
            ) : e.reasons ? (
              <p className="op-muted">No risk indicators on file.</p>
            ) : (
              <p className="op-muted">Risk reasons are not included in this backend response.</p>
            )}
            <div className="ent-reco">
              <span>Recommendation</span>
              <strong>{RECOMMENDATION_LABEL[e.recommendation] ?? 'Not available'}</strong>
              {e.recommendation && <code className="mono">{e.recommendation}</code>}
            </div>
          </>
        )}

        {tab === 'Transactions' && (
          <>
            <PanelHead title="Transactions" note="Payments sent to this recipient" />
            {e.transactions ? (
              <TransactionList items={e.transactions} />
            ) : (
              <p className="op-muted">Transaction details are not included in this backend response.</p>
            )}
          </>
        )}

        {tab === 'Reports' && (
          <>
            <PanelHead title="Fraud reports" note="Submitted by customers" />
            {e.reports ? (
              <ReportList items={e.reports} total={e.reports_total} />
            ) : (
              <p className="op-muted">
                {e.reports_count} report records are counted; report details are not included in this response.
              </p>
            )}
          </>
        )}

        {tab === 'Relationships' && (
          <>
            <PanelHead title="Relationships" note="Accounts connected to this recipient" />
            {e.related_accounts ? (
              <RelatedAccounts items={e.related_accounts} />
            ) : (
              <p className="op-muted">
                {e.suspicious_relationship_count} suspicious relationship records are counted; account details are not included in this response.
              </p>
            )}
            <p style={{ marginTop: 24, fontSize: 14 }}>
              <Link to={`/admin/entity/${e.phone}/graph`} style={{ color: 'var(--ink)' }}>
                Open full graph →
              </Link>
            </p>
          </>
        )}

        {tab === 'Risk history' && (
          <>
            <PanelHead
              title="Risk history"
              note="Score movement over the last 90 days"
              aside={
                <div className={`ent-current ${levelClass(e.level)}`}>
                  <strong>{e.score}</strong>
                  <small>Current score</small>
                </div>
              }
            />
            {e.risk_history ? (
              <RiskChart history={e.risk_history} level={e.level} />
            ) : (
              <p className="op-muted">Risk history is not included in this backend response.</p>
            )}
          </>
        )}

        {tab === 'Cases' && (
          <>
            <PanelHead title="Cases" note="Investigations opened for this recipient" />
            {e.cases ? e.cases.length === 0 ? (
              <p className="op-muted">No cases have been opened for this recipient.</p>
            ) : (
              <ul className="ent-cases">
                {e.cases.map((c) => (
                  <li key={c.id}>
                    <Link className="mono" to={`/admin/cases/${c.id}`}>{formatCaseId(c.id)}</Link>
                    <span className={`op-status op-status-${c.status.toLowerCase()}`}>
                      <i aria-hidden="true" />
                      {STATUS_LABEL[c.status]}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="op-muted">Case details are not included in this backend response.</p>
            )}
          </>
        )}
      </div>
    </div>
  )
}