import { formatDateTime, formatReportId } from '../../utils/format'
import './investigation.css'

export default function ReportList({ items, total }) {
  if (items.length === 0) {
    return <p className="op-muted">No fraud reports on file.</p>
  }
  return (
    <>
      <p className="op-muted iv-count">
        Showing {items.length} of {total} reports
      </p>
      {items.map((r) => (
        <p className="iv-report" key={r.id}>
          <span className="mono">
            {formatReportId(r.id)} · {formatDateTime(r.created_at)} · {r.scam_type}
          </span>
          {r.summary}
        </p>
      ))}
    </>
  )
}
