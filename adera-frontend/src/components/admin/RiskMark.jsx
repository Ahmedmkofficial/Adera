import '../risk/risk.css'
import { levelClass, levelLabel } from '../../utils/risk'

export default function RiskMark({ score, level }) {
  return (
    <span className={`op-mark ${levelClass(level)}`}>
      <span
        className="op-mark-line"
        role="img"
        aria-label={score == null ? 'Score unavailable' : `Score ${score} out of 100`}
      >
        {score != null && <span className="op-mark-dot" style={{ left: `${score}%` }} />}
      </span>
      <span className="op-level">{levelLabel(level)}</span>
    </span>
  )
}