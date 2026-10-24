import { formatDateTime } from '../../utils/format'
import './investigation.css'

export default function TransactionList({ items }) {
  if (items.length === 0) {
    return <p className="op-muted">No transactions recorded.</p>
  }
  return (
    <div className="iv-table">
      <div className="iv-tr iv-tr-head">
        <span>Date</span>
        <span>Sent from</span>
        <span>Amount</span>
        <span>Transaction ID</span>
      </div>
      {items.map((t) => (
        <div className="iv-tr" key={t.id}>
          <span>{formatDateTime(t.created_at)}</span>
          <span className="mono">{t.counterparty}</span>
          <span>{t.amount.toLocaleString('en-US')} ETB</span>
          <span className="mono">{t.id}</span>
        </div>
      ))}
    </div>
  )
}
