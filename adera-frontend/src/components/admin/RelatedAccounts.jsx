import { Link } from 'react-router-dom'
import { levelClass, levelLabel } from '../../utils/risk'
import './investigation.css'

export default function RelatedAccounts({ items }) {
  if (items.length === 0) {
    return <p className="op-muted">No related accounts found.</p>
  }
  return (
    <ul className="iv-rel">
      {items.map((a, index) => (
        <li key={`${a.phone}:${a.relation}:${index}`} className={levelClass(a.level)}>
          <Link className="mono" to={`/admin/entity/${a.phone}`}>{a.phone}</Link>
          <span className="mono op-muted">{a.relation}</span>
          <span className="iv-rel-level">{levelLabel(a.level)}</span>
        </li>
      ))}
    </ul>
  )
}
