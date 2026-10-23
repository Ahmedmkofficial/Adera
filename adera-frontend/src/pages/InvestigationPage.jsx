import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Button from '../components/ui/Button'
import RiskRuler from '../components/risk/RiskRuler'
import Thread from '../components/risk/Thread'
import TransactionList from '../components/admin/TransactionList'
import ReportList from '../components/admin/ReportList'
import RelatedAccounts from '../components/admin/RelatedAccounts'
import useCountUp from '../utils/useCountUp'
import { createCase, getAlert } from '../services/api'
import { STATUS_LABEL, formatCaseId } from '../utils/format'
import { RECOMMENDATION_LABEL, levelClass, levelLabel } from '../utils/risk'
import '../components/admin/investigation.css'

function Summary({ d, opening, onOpenCase }) {
  const score = useCountUp(d.score ?? 0)

  return (
    <aside className={`iv-summary ${levelClass(d.level)}`} aria-label="Alert summary">
      <p className="op-eyebrow">ALERT · {STATUS_LABEL[d.status].toUpperCase()}</p>
      <h1>Alert #{d.id}</h1>
      <p className="iv-recipient mono">{d.recipient_phone}</p>

      <div
        className="iv-score"
        role="img"
        aria-label={d.score == null ? 'Risk score unavailable' : `Risk score ${d.score} out of 100`}
      >
        {d.score == null ? '—' : score}
        {d.score != null && <span>/100</span>}
      </div>
      <div className="iv-level">{levelLabel(d.level)}</div>

      {d.score != null && <RiskRuler score={d.score} level={d.level} />}

      <div className="iv-reco">
        <span>Recommendation</span>
        <strong>        {RECOMMENDATION_LABEL[d.recommendation] ?? 'Not available'}</strong>
          {d.recommendation && <code className="mono">{d.recommendation}</code>}
      </div>

      {d.case_id ? (
        <Link className="ad-btn ad-btn-primary iv-link-btn" to={`/admin/cases/${d.case_id}`}>
          View case {formatCaseId(d.case_id)}
        </Link>
      ) : (
        <Button onClick={onOpenCase} disabled={opening}>
          {opening ? 'Opening…' : 'Open case'}
        </Button>
      )}

      <Link className="iv-entity-link" to={`/admin/entity/${d.recipient_phone}`}>
        View entity profile →
      </Link>
    </aside>
  )
}

function Section({ title, children }) {
  return (
    <section className="iv-section">
      <span className="iv-section-node" aria-hidden="true" />
      <h3>{title}</h3>
      {children}
    </section>
  )
}

export default function InvestigationPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [detail, setDetail] = useState(undefined) // undefined = loading, null = not found
  const [error, setError] = useState('')
  const [opening, setOpening] = useState(false)

  useEffect(() => {
    let cancelled = false
    getAlert(id)
      .then((data) => {
        if (!cancelled) setDetail(data)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load this alert. Please refresh the page.')
      })
    return () => {
      cancelled = true
    }
  }, [id])

  async function handleOpenCase() {
    setOpening(true)
    setError('')
    try {
      const created = await createCase(detail)
      navigate(`/admin/cases/${created.id}`)
    } catch (error) {
      setError(error.message || 'Could not open a case. Please try again.')
      setOpening(false)
    }
  }

  if (error && !detail) {
    return (
      <div className="op-page">
        <p className="op-error" role="alert">{error}</p>
      </div>
    )
  }
  if (detail === undefined) {
    return (
      <div className="op-page">
        <p className="op-empty">Loading investigation…</p>
      </div>
    )
  }
  if (detail === null) {
    return (
      <div className="op-page">
        <h1 className="iv-notfound">Alert not found</h1>
        <p className="op-muted">
          There is no alert with the number {id}. <Link to="/admin/alerts">Back to all alerts</Link>
        </p>
      </div>
    )
  }

  const d = detail
  const count = d.reasons.length

  return (
    <div className="iv">
      <Summary d={d} opening={opening} onOpenCase={handleOpenCase} />

      <div className="iv-detail">
        <p className="op-eyebrow">INVESTIGATION</p>
        <h2 className="iv-lead">
          {count} risk {count === 1 ? 'indicator contributes' : 'indicators contribute'} to this score.
        </h2>
        {error && <p className="op-error" role="alert">{error}</p>}

        <div className="iv-thread">
          <Section title="Why this alert exists">
            <Thread items={d.reasons} level={d.level} />
          </Section>

          <Section title="Transactions">
            <TransactionList items={d.transactions} />
          </Section>

          <Section title="Fraud reports">
            <ReportList items={d.reports} total={d.reports_total} />
          </Section>

          <Section title="Related accounts">
            <RelatedAccounts items={d.related_accounts} />
          </Section>
        </div>
      </div>
    </div>
  )
}
