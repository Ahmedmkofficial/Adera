import { useEffect, useRef } from 'react'
import Button from '../ui/Button'
import RiskRuler from './RiskRuler'
import Thread from './Thread'
import HoldButton from './HoldButton'
import useCountUp from '../../utils/useCountUp'
import { RECOMMENDATION_LABEL, levelClass, levelLabel } from '../../utils/risk'
import './risk.css'

export default function RiskCard({
  result,
  onCancel,
  onVerify,
  onContinue,
  onSendAnyway,
  onClose,
  busy = false,
}) {
  const sheetRef = useRef(null)
  const score = useCountUp(result.score)
  const isLow = result.level === 'LOW'

  // move keyboard focus into the sheet when it opens
  useEffect(() => {
    sheetRef.current?.focus()
  }, [])

  // Escape closes the sheet
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && !busy && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose, busy])

  return (
    <>
      <div className="rk-scrim" onClick={busy ? undefined : onClose} />
      <section
        ref={sheetRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="rk-title"
        className={`rk-sheet ${levelClass(result.level)}`}
      >
        <div className="rk-handle" />

        <div className="rk-score-row">
          <div className="rk-score">
            {score}
            <span>/100</span>
          </div>
          <h2 id="rk-title" className="rk-level">
            {levelLabel(result.level)}
          </h2>
        </div>

        <RiskRuler score={result.score} level={result.level} />

        <h3 className="rk-why">Why?</h3>
        <Thread items={result.reasons} level={result.level} />

        <div className="rk-reco">
          <span>Recommendation</span>
          <strong>{RECOMMENDATION_LABEL[result.recommendation]}</strong>
        </div>

        <div className="rk-actions">
          {isLow ? (
            <>
              <Button onClick={onContinue} disabled={busy}>{busy ? 'Sending…' : 'Continue'}</Button>
              <Button variant="tertiary" onClick={onCancel} disabled={busy}>Cancel</Button>
            </>
          ) : (
            <>
              <Button onClick={onCancel} disabled={busy}>Cancel payment</Button>
              <Button variant="secondary" onClick={onVerify} disabled={busy}>Verify recipient</Button>
              <div className="rk-hold-wrap">
                <HoldButton onComplete={() => !busy && onSendAnyway()}>
                  {busy ? 'Sending…' : 'Hold to send anyway'}
                </HoldButton>
              </div>
            </>
          )}
        </div>
      </section>
    </>
  )
}