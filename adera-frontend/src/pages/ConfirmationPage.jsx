import { useEffect, useRef } from 'react'
import { Navigate, useLocation, useNavigate, useParams } from 'react-router-dom'
import CustomerShell from '../components/customer/CustomerShell'
import Button from '../components/ui/Button'
import { formatDateTime, formatTxnId } from '../utils/format'
import { levelClass, levelLabel } from '../utils/risk'

const CONTENT = {
  sent: {
    icon: 'check',
    title: 'Payment sent',
    body: 'Simulated payment. No money was moved.',
  },
  cancelled: {
    icon: 'cross',
    title: 'Payment cancelled',
    body: 'No money was sent.',
  },
  reported: {
    icon: 'check',
    title: 'Report submitted',
    body: 'Thank you for helping improve fraud intelligence.',
  },
}

export default function ConfirmationPage() {
  const { type } = useParams()
  const { state } = useLocation()
  const navigate = useNavigate()
  const titleRef = useRef(null)

  // move focus to the title so screen readers announce the result
  useEffect(() => {
    titleRef.current?.focus()
  }, [])

  // an unknown address like /confirmation/banana goes home
  if (!Object.hasOwn(CONTENT, type)) return <Navigate to="/" replace />

  const { icon, title, body } = CONTENT[type]
  const phone = state?.phone
  const amount = state?.amount
  const reference = state?.reference
  const createdAt = state?.createdAt
  const level = state?.level
  const showSummary = type !== 'reported' && phone && amount

  return (
    <CustomerShell>
      <div className="cu-confirm">
        <svg className="cu-confirm-icon" viewBox="0 0 64 64" aria-hidden="true">
          {icon === 'check' ? (
            <path pathLength="1" d="M16 33 L27 44 L48 20" />
          ) : (
            <path pathLength="1" d="M20 20 L44 44 M44 20 L20 44" />
          )}
        </svg>

        <h1 ref={titleRef} tabIndex={-1} className="cu-confirm-title">
          {title}
        </h1>
        <p className="cu-confirm-body">{body}</p>

        {showSummary && (
          <dl className="cu-summary">
            <div>
              <dt>Amount</dt>
              <dd>{Number(amount).toLocaleString('en-US')} ETB</dd>
            </div>
            <div>
              <dt>Recipient</dt>
              <dd className="mono">{phone}</dd>
            </div>
            {type === 'sent' && reference && (
              <div>
                <dt>Reference</dt>
                <dd className="mono">{formatTxnId(reference)}</dd>
              </div>
            )}
            {type === 'sent' && createdAt && (
              <div>
                <dt>Time</dt>
                <dd>{formatDateTime(createdAt)}</dd>
              </div>
            )}
            {type === 'sent' && level && (
              <div>
                <dt>Risk check</dt>
                <dd className={`cu-risk-word ${levelClass(level)}`}>{levelLabel(level)}</dd>
              </div>
            )}
          </dl>
        )}
      </div>

      <div className="cu-bottom">
        <Button onClick={() => navigate('/')}>Done</Button>
        {showSummary && (
          <Button
            variant="tertiary"
            style={{ marginTop: 8 }}
            onClick={() => navigate('/report', { state: { phone } })}
          >
            Report this recipient
          </Button>
        )}
      </div>
    </CustomerShell>
  )
}