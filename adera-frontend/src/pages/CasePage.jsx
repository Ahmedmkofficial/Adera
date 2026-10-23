import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Button from '../components/ui/Button'
import { getCase, submitDecision } from '../services/api'
import {
  DECISION_LABEL,
  STATUS_LABEL,
  formatAlertId,
  formatCaseId,
  formatDateTime,
} from '../utils/format'
import { RECOMMENDATION_LABEL, levelClass, levelLabel } from '../utils/risk'
import '../components/admin/case.css'

const EVIDENCE = [
  ['reports', 'reports'],
  ['recent', 'recent reports'],
  ['scam_cases', 'scam cases'],
  ['related_accounts', 'related accounts'],
]

// A new case number in the address starts the page fresh (key = id)
export default function CaseRoute() {
  const { id } = useParams()
  return <CasePage key={id} id={id} />
}

function CasePage({ id }) {
  const [c, setCase] = useState(undefined) // undefined = loading, null = not found
  const [error, setError] = useState('')
  const [confirming, setConfirming] = useState(null) // null | 'FRAUD' | 'FALSE_POSITIVE'
  const [saving, setSaving] = useState(false)
  const [focusTick, setFocusTick] = useState(0)
  const headingRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    getCase(id)
      .then((data) => {
        if (!cancelled) setCase(data)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load this case. Please refresh the page.')
      })
    return () => {
      cancelled = true
    }
  }, [id])

  // when the decision panel changes, move keyboard focus to its heading
  useEffect(() => {
    if (focusTick > 0) headingRef.current?.focus()
  }, [focusTick])

  function openConfirm(decision) {
    setConfirming(decision)
    setFocusTick((t) => t + 1)
  }

  async function record(decision) {
    setSaving(true)
    setError('')
    try {
      const updated = await submitDecision(c.id, decision)
      setCase(updated)
      setConfirming(null)
      setFocusTick((t) => t + 1)
    } catch {
      setError('Could not record the decision. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (error && !c) {
    return (
      <div className="op-page">
        <p className="op-error" role="alert">{error}</p>
      </div>
    )
  }
  if (c === undefined) {
    return (
      <div className="op-page">
        <p className="op-empty">Loading case…</p>
      </div>
    )
  }
  if (c === null) {
    return (
      <div className="op-page">
        <h1 className="iv-notfound">Case not found</h1>
        <p className="op-muted">
          There is no case with the number {id}. <Link to="/admin/cases">Back to all cases</Link>
        </p>
      </div>
    )
  }

  const closed = c.status === 'CLOSED'
  const needsInfo = c.decision === 'NEEDS_MORE_INFORMATION'

  return (
    <div className="op-page">
      <div className="cs-head">
        <div>
          <div className="cs-kicker">
            <span className={`op-status op-status-${c.status.toLowerCase()}`}>
              <i aria-hidden="true" />
              {STATUS_LABEL[c.status]}
            </span>
            <span className="mono">SUBJECT · {c.subject}</span>
          </div>
          <h1>Case {formatCaseId(c.id)}</h1>
        </div>
        <nav className="cs-links" aria-label="Related pages">
          <Link to={`/admin/alerts/${c.alert_id}`}>View alert {formatAlertId(c.alert_id)} →</Link>
          <Link to={`/admin/entity/${c.subject}`}>View entity profile →</Link>
        </nav>
      </div>

      <div className="cs-cols">
        <section aria-labelledby="cs-history">
          <h2 className="op-eyebrow cs-eyebrow-h" id="cs-history">HISTORY</h2>
          <ol className="cs-timeline">
            {c.events.map((ev, i) => (
              <li key={`${ev.time}-${ev.title}`} className={i === 0 ? levelClass(c.level) : ''}>
                <span className="cs-node" aria-hidden="true" />
                {ev.time && <time className="mono" dateTime={ev.time}>{formatDateTime(ev.time)}</time>}
                <h3>{ev.title}</h3>
                <p>{ev.body}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="cs-evidence" aria-labelledby="cs-evidence-title">
          <p className="op-eyebrow">EVIDENCE</p>
          <h2 id="cs-evidence-title">Evidence summary</h2>
          <ul className="cs-evidence-list">
            {EVIDENCE.map(([key, label]) => (
              <li key={key} className={c.evidence[key] > 0 ? levelClass(c.level) : ''}>
                <span className="cs-node" aria-hidden="true" />
                <strong>{c.evidence[key]}</strong>
                <span>{label}</span>
              </li>
            ))}
          </ul>

          <div className="cs-payment">
            <span className="op-eyebrow">LATEST PAYMENT</span>
            {c.payment ? (
              <>
                <strong>{c.payment.amount.toLocaleString('en-US')} ETB</strong>
                <span className="mono">
                  {c.payment.txn_id} · {formatDateTime(c.payment.created_at)}
                </span>
              </>
            ) : (
              <span className="op-muted">No payment record is available for this case.</span>
            )}
          </div>
        </section>

        <aside className="cs-decision" aria-live="polite" aria-label="Case decision">
          {closed ? (
            <>
              <h2 ref={headingRef} tabIndex={-1}>Decision recorded</h2>
              <div className="cs-stamp mono">
                {c.decision} · RECORDED
                <br />
                {c.decided_at ? formatDateTime(c.decided_at) : 'Timestamp not recorded'}
              </div>
              <p className="cs-note-plain">
                The outcome is now part of this case&apos;s history, and the case is closed.
              </p>
              <dl className="cs-facts">
                <div>
                  <dt>Outcome</dt>
                  <dd>{DECISION_LABEL[c.decision]}</dd>
                </div>
                <div>
                  <dt>Recorded by</dt>
                  <dd>{c.decided_by ?? 'Not recorded'}</dd>
                </div>
              </dl>
            </>
          ) : confirming ? (
            <div className="cs-confirm">
              <h2 ref={headingRef} tabIndex={-1}>
                {confirming === 'FRAUD'
                  ? 'Record this case as fraud?'
                  : 'Record this case as a false positive?'}
              </h2>
              <p className="cs-note-plain">This closes the case and cannot be undone.</p>
              {error && <p className="op-error cs-error" role="alert">{error}</p>}
              <div className="cs-actions">
                <Button onClick={() => record(confirming)} disabled={saving}>
                  {saving ? 'Recording…' : 'Confirm'}
                </Button>
                <Button variant="secondary" onClick={() => openConfirm(null)} disabled={saving}>
                  Back
                </Button>
              </div>
            </div>
          ) : (
            <>
              <h2 ref={headingRef} tabIndex={-1}>Record an outcome</h2>

              {needsInfo && (
                <p className="cs-note">
                  More information was requested
                  {c.decided_at && <> · {formatDateTime(c.decided_at)}</>}
                  <br />
                  The case stays open until a final outcome is recorded.
                </p>
              )}

              <dl className="cs-facts">
                <div>
                  <dt>Score</dt>
                  <dd className={c.level ? `cs-lvl ${levelClass(c.level)}` : ''}>
                    {c.score ?? 'Not available'}
                  </dd>
                </div>
                <div>
                  <dt>Level</dt>
                  <dd className={c.level ? `cs-lvl ${levelClass(c.level)}` : ''}>
                    {c.level ? levelLabel(c.level) : 'Not available'}
                  </dd>
                </div>
                <div>
                  <dt>Recommendation</dt>
                  <dd>
                    {RECOMMENDATION_LABEL[c.recommendation] ?? 'Not available'}
                    {c.recommendation && <code className="mono">{c.recommendation}</code>}
                  </dd>
                </div>
              </dl>

              {error && <p className="op-error cs-error" role="alert">{error}</p>}

              <div className="cs-actions">
                <Button onClick={() => openConfirm('FRAUD')}>Mark as fraud</Button>
                <Button variant="secondary" onClick={() => openConfirm('FALSE_POSITIVE')}>
                  False positive
                </Button>
                {!needsInfo && (
                  <Button
                    variant="tertiary"
                    onClick={() => record('NEEDS_MORE_INFORMATION')}
                    disabled={saving}
                  >
                    {saving ? 'Saving…' : 'Needs more information'}
                  </Button>
                )}
              </div>
            </>
          )}
        </aside>
      </div>
    </div>
  )
}