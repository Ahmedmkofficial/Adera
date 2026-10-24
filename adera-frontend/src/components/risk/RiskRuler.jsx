import { levelClass } from '../../utils/risk'

export default function RiskRuler({ score, level }) {
  return (
    <div
      className={`rk-ruler ${levelClass(level)}`}
      role="img"
      aria-label={`Risk score ${score} out of 100`}
    >
      <div className="rk-line">
        <span className="rk-tick" style={{ left: '25%' }} />
        <span className="rk-tick" style={{ left: '50%' }} />
        <span className="rk-tick" style={{ left: '75%' }} />
        <span className="rk-dot" style={{ left: `${score}%` }} />
      </div>
      <div className="rk-labels" aria-hidden="true">
        <span>0</span><span>25</span><span>50</span><span>75</span><span>100</span>
      </div>
    </div>
  )
}