import { levelClass } from '../../utils/risk'
import { formatShortDate } from '../../utils/format'
import '../risk/risk.css'
import './entity.css'

const W = 1000
const H = 320
const PAD = 10

const xFor = (i, n) => PAD + (i / (n - 1)) * (W - PAD * 2)
const yFor = (score) => PAD + (1 - score / 100) * (H - PAD * 2)

export default function RiskChart({ history, level }) {
  const n = history.length
  const points = history.map((p, i) => [xFor(i, n), yFor(p.score)])
  const line = points
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`)
    .join(' ')
  const [endX, endY] = points[n - 1]
  const first = history[0]
  const last = history[n - 1]

  return (
    <figure className={`ent-chart ${levelClass(level)}`}>
      <div className="ent-ylabels" aria-hidden="true">
        {[100, 75, 50, 25, 0].map((v) => (
          <span key={v} style={{ top: `${(yFor(v) / H) * 100}%` }}>{v}</span>
        ))}
      </div>

      <div className="ent-plot">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          role="img"
          aria-label={`Risk score moved from ${first.score} to ${last.score} between ${formatShortDate(first.date)} and ${formatShortDate(last.date)}`}
        >
          {[0, 25, 50, 75, 100].map((v) => (
            <line key={v} className="ent-gridline" x1="0" x2={W} y1={yFor(v)} y2={yFor(v)} />
          ))}
          <path className="ent-line" d={line} />
          <circle className="ent-end" cx={endX} cy={endY} r="6" />
        </svg>
      </div>

      <div className="ent-xlabels" aria-hidden="true">
        {history.map((p, i) => (
          <span key={p.date} style={{ left: `${(xFor(i, n) / W) * 100}%` }}>
            {formatShortDate(p.date)}
          </span>
        ))}
      </div>

      {/* the same numbers as text, for screen readers */}
      <ul className="sr-only">
        {history.map((p) => (
          <li key={p.date}>{formatShortDate(p.date)}: score {p.score}</li>
        ))}
      </ul>
    </figure>
  )
}