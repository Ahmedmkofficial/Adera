// The API sends plain numbers; the screen decides how to show them.
export const formatAlertId = (id) => `ALR-${id}`

export const STATUS_LABEL = {
  OPEN: 'Open',
  IN_CASE: 'In case',
  CLOSED: 'Closed',
}

export function timeAgo(iso) {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return days === 1 ? 'Yesterday' : `${days}d ago`
}

export const formatCaseId = (id) => `#${id}`
export const formatReportId = (id) => `REPORT-${id}`

export function formatDateTime(iso) {
  return new Date(iso).toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function formatShortDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

export const DECISION_LABEL = {
  FRAUD: 'Fraud',
  FALSE_POSITIVE: 'False positive',
  NEEDS_MORE_INFORMATION: 'Needs more information',
}
export const formatTxnId = (id) => `TXN-${id}`
