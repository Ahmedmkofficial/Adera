// Shapes match the agreed POST /risk/check response.
// Scores only use sums the engine's weights can produce
// (20 + 15 + 25 + 15 + 15 + 10), unlike the Figma file's 48 and 18.
const RISK_BY_LEVEL = {
  CRITICAL: {
    score: 75,
    level: 'CRITICAL',
    recommendation: 'STOP_AND_VERIFY',
    reasons: [
      'Multiple independent fraud reports',
      'Recent fraud reports exist',
      'Previous scam case exists',
      'Suspicious account relationship detected',
    ],
  },
  HIGH: {
    score: 50,
    level: 'HIGH',
    recommendation: 'VERIFY',
    reasons: [
      'Multiple independent fraud reports',
      'Recent fraud reports exist',
      'Repeated scam pattern',
    ],
  },
  MODERATE: {
    score: 25,
    level: 'MODERATE',
    recommendation: 'REVIEW',
    reasons: ['Recent fraud reports exist', 'Unusual transaction behavior'],
  },
  LOW: {
    score: 10,
    level: 'LOW',
    recommendation: 'ALLOW',
    reasons: ['Unusual transaction behavior'],
  },
}

// Test numbers. Only 0912345678 comes from the project PDF;
// the others are my own so you can see every level.
const PHONE_TO_LEVEL = {
  '0912345678': 'CRITICAL',
  '0911111111': 'HIGH',
  '0922222222': 'MODERATE',
}

export function mockCheckRisk(recipient_phone) {
  const level = PHONE_TO_LEVEL[recipient_phone] ?? 'LOW'
  // fake network delay so the loading state is visible
  return new Promise((resolve) =>
    setTimeout(() => resolve(RISK_BY_LEVEL[level]), 500),
  )
}
 
// Fake "report submitted" call. Later it becomes POST /reports.
export function mockSubmitReport(report) {
  return new Promise((resolve) =>
    setTimeout(() => resolve({ id: 'mock-report', ...report }), 600),
  )
}

// ---------- Analyst side ----------
const delay = (value, ms = 400) =>
  new Promise((resolve) => setTimeout(() => resolve(value), ms))

const minutesAgo = (m) => new Date(Date.now() - m * 60 * 1000).toISOString()

// ONE shared source for alerts. Scores are multiples of 5 (what the engine's
// weights can produce) and levels follow the agreed bands:
// 0-24 LOW, 25-49 MODERATE, 50-74 HIGH, 75-100 CRITICAL.
export const ALERTS = [
  { id: 1042, recipient_phone: '0912345678', score: 75, level: 'CRITICAL', reason: 'Multiple independent fraud reports', status: 'OPEN', created_at: minutesAgo(4) },
  { id: 1039, recipient_phone: '0927804412', score: 65, level: 'HIGH', reason: 'Suspicious account relationship detected', status: 'IN_CASE', created_at: minutesAgo(18) },
  { id: 1038, recipient_phone: '0911568204', score: 40, level: 'MODERATE', reason: 'Unusual transaction behavior', status: 'OPEN', created_at: minutesAgo(42) },
  { id: 1034, recipient_phone: '0944103721', score: 85, level: 'CRITICAL', reason: 'Repeated scam pattern', status: 'IN_CASE', created_at: minutesAgo(65) },
  { id: 1031, recipient_phone: '0930928540', score: 60, level: 'HIGH', reason: 'Previous scam case exists', status: 'CLOSED', created_at: minutesAgo(130) },
  { id: 1027, recipient_phone: '0918200972', score: 30, level: 'MODERATE', reason: 'Recent fraud reports exist', status: 'CLOSED', created_at: minutesAgo(190) },
]

export function mockGetAlerts() {
  return delay(ALERTS)
}

export function mockUpdateAlertStatus(id, status) {
  const alert = ALERTS.find((item) => item.id === Number(id))
  if (!alert) return Promise.reject(new Error('Alert not found'))
  if (!['OPEN', 'IN_CASE', 'CLOSED'].includes(status)) {
    return Promise.reject(new Error('Invalid alert status'))
  }
  alert.status = status
  return delay(alert)
}

// The dashboard totals come from the project PDF's example.
export function mockGetDashboardSummary() {
  return delay({ alerts: 24, critical: 3, high: 8, open_cases: 12, reports: 137 })
}

// ---------- Alert investigation ----------
// What each factor is worth in the Risk Engine (from the project PDF,
// with "repeated pattern" at 15 so the total is 100):
// reports 20, recent 15, case 25, relationship 15, pattern 15, behavior 10
const FACTOR_TEXT = {
  reports: 'Multiple independent fraud reports',
  recent: 'Recent fraud reports exist',
  case: 'Previous scam case exists',
  relationship: 'Suspicious account relationship detected',
  pattern: 'Repeated scam pattern',
  behavior: 'Unusual transaction behavior',
}

// Every list below adds up exactly to that alert's score.
const ALERT_FACTORS = {
  1042: ['reports', 'recent', 'case', 'relationship'], // 20+15+25+15 = 75
  1039: ['case', 'relationship', 'pattern', 'behavior'], // 25+15+15+10 = 65
  1038: ['recent', 'pattern', 'behavior'], // 15+15+10 = 40
  1034: ['reports', 'recent', 'case', 'pattern', 'behavior'], // 20+15+25+15+10 = 85
  1031: ['reports', 'case', 'relationship'], // 20+25+15 = 60
  1027: ['recent', 'relationship'], // 15+15 = 30
}

// alert id -> case id (null = no case yet)
const CASE_BY_ALERT = { 1039: 1018, 1034: 1009, 1031: 1006, 1027: 998 }
let nextCaseId = 1022

const SENDERS = ['0911204933', '0927889041', '0930774120']
const AMOUNTS = [5000, 12400, 2750]
const SCAM_TYPES = ['Impersonation', 'Fake investment', 'Prize or lottery']
const SUMMARIES = [
  'Reported after an unsolicited call asking for urgent payment.',
  'Payment requested using urgent language.',
  'Recipient details matched an earlier report.',
]

function buildDetail(alert) {
  const factors = ALERT_FACTORS[alert.id] ?? []
  const hasReports = factors.includes('reports')
  const reportCount = hasReports ? 3 : 2

  return {
    ...alert,
    recommendation: RISK_BY_LEVEL[alert.level].recommendation,
    reasons: factors.map((f) => FACTOR_TEXT[f]),
    transactions: SENDERS.map((counterparty, i) => ({
      id: `TXN-${883104 - i * 1178}`,
      created_at: minutesAgo(8 + i * 1440),
      counterparty,
      amount: AMOUNTS[i],
    })),
    reports_total: hasReports ? 7 : reportCount,
    reports: Array.from({ length: reportCount }, (_, i) => ({
      id: (alert.id % 100) + i * 13,
      created_at: minutesAgo(30 + i * 1500),
      scam_type: SCAM_TYPES[i],
      summary: SUMMARIES[i],
    })),
    related_accounts: factors.includes('relationship')
      ? [
          { phone: '0927804412', relation: 'SHARED_PHONE', level: 'HIGH' },
          { phone: '0911568204', relation: 'TRANSACTION', level: 'MODERATE' },
        ].filter((a) => a.phone !== alert.recipient_phone)
      : [],
    case_id: CASE_BY_ALERT[alert.id] ?? null,
  }
}

// Returns null when the alert does not exist.
export function mockGetAlert(id) {
  const alert = ALERTS.find((a) => a.id === Number(id))
  return delay(alert ? buildDetail(alert) : null)
}

// Opens a case for an alert. Note: this "database" resets when you refresh.
export function mockCreateCase(alertId) {
  const alert = ALERTS.find((a) => a.id === Number(alertId))
  if (!alert) return Promise.reject(new Error('Alert not found'))
  if (!CASE_BY_ALERT[alert.id]) {
    CASE_BY_ALERT[alert.id] = alert.id === 1042 ? 1021 : nextCaseId++
    alert.status = 'IN_CASE'
  }
  return delay({
    id: CASE_BY_ALERT[alert.id],
    alert_id: alert.id,
    subject: alert.recipient_phone,
    status: 'OPEN',
    risk_level: alert.level,
  })
}

// ---------- Entity profile ----------
// Risk-score history: 7 points, 15 days apart, ending at the current score.
// Every value is a multiple of 5, like the engine's weights.
function buildHistory(score) {
  const fractions = [0.1, 0.2, 0.3, 0.5, 0.65, 0.85, 1]
  return fractions.map((f, i) => ({
    date: minutesAgo((fractions.length - 1 - i) * 15 * 1440),
    score: i === fractions.length - 1 ? score : Math.round((score * f) / 5) * 5,
  }))
}

// Returns null when we have no intelligence on this number.
export function mockGetEntity(phone) {
  const alert = ALERTS.find((a) => a.recipient_phone === phone)
  if (!alert) return delay(null)

  const d = buildDetail(alert)
  const factors = ALERT_FACTORS[alert.id] ?? []

  return delay({
    phone,
    score: d.score,
    level: d.level,
    recommendation: d.recommendation,
    reasons: d.reasons,
    reports_count: d.reports_total,
    // "recent" can never be more than the total
    recent_reports: factors.includes('recent') ? Math.min(3, d.reports_total) : 0,
    scam_cases: factors.includes('case') ? 2 : 0,
    related_accounts_count: d.related_accounts.length,
    first_observed: minutesAgo(150 * 1440),
    last_activity: d.created_at,
    transactions: d.transactions,
    reports: d.reports,
    reports_total: d.reports_total,
    related_accounts: d.related_accounts,
    risk_history: buildHistory(d.score),
    cases: d.case_id
      ? [{ id: d.case_id, status: alert.status === 'CLOSED' ? 'CLOSED' : 'OPEN' }]
      : [],
  })
}


// ---------- Cases ----------
const MOCK_ANALYST = 'Admin' // later: the signed-in analyst, from the API
const DECISIONS = ['FRAUD', 'FALSE_POSITIVE', 'NEEDS_MORE_INFORMATION']

const DECISION_EVENT = {
  FRAUD: { title: 'Marked as fraud', body: 'The case was closed with the outcome FRAUD.' },
  FALSE_POSITIVE: { title: 'Marked as false positive', body: 'The case was closed with the outcome FALSE_POSITIVE.' },
  NEEDS_MORE_INFORMATION: { title: 'More information requested', body: 'The case stays open until a final outcome is recorded.' },
}

// Cases that already exist when the app starts (times are minutes ago).
const SEED_CASES = {
  1018: { opened: 15, decision: 'NEEDS_MORE_INFORMATION', decided: 12, closed: false },
  1009: { opened: 55, decision: null, decided: null, closed: false },
  1006: { opened: 120, decision: 'FALSE_POSITIVE', decided: 100, closed: true },
  998: { opened: 180, decision: 'FRAUD', decided: 150, closed: true },
}

const CASE_STORE = {} // case id -> case record (built the first time it is needed)

function caseIdToAlert(caseId) {
  const entry = Object.entries(CASE_BY_ALERT).find(([, cid]) => cid === caseId)
  return entry ? ALERTS.find((a) => a.id === Number(entry[0])) : undefined
}

function buildCase(alert, caseId) {
  const seed = SEED_CASES[caseId]
  const d = buildDetail(alert)
  const factors = ALERT_FACTORS[alert.id] ?? []
  const openedAt = minutesAgo(seed ? seed.opened : 0)

  const events = [
    { time: alert.created_at, title: 'Alert raised', body: `Risk score reached ${alert.score}.` },
    { time: openedAt, title: 'Case opened', body: 'An analyst opened this case from the alert.' },
  ]
  let decision = null
  let decidedAt = null
  if (seed?.decision) {
    decision = seed.decision
    decidedAt = minutesAgo(seed.decided)
    events.push({ time: decidedAt, ...DECISION_EVENT[decision] })
  }

  const payment = d.transactions[0]
  return {
    id: caseId,
    alert_id: alert.id,
    subject: alert.recipient_phone,
    score: alert.score,
    level: alert.level,
    recommendation: d.recommendation,
    status: seed?.closed ? 'CLOSED' : 'OPEN',
    decision,
    decided_by: decision ? MOCK_ANALYST : null,
    decided_at: decidedAt,
    created_at: openedAt,
    updated_at: decidedAt ?? openedAt,
    events,
    evidence: {
      reports: d.reports_total,
      recent: factors.includes('recent') ? Math.min(3, d.reports_total) : 0,
      scam_cases: factors.includes('case') ? 2 : 0,
      related_accounts: d.related_accounts.length,
    },
    payment: { amount: payment.amount, txn_id: payment.id, created_at: payment.created_at },
  }
}

function ensureCase(caseId) {
  const id = Number(caseId)
  if (!CASE_STORE[id]) {
    const alert = caseIdToAlert(id)
    if (!alert) return null
    CASE_STORE[id] = buildCase(alert, id)
  }
  return CASE_STORE[id]
}

const summarize = (c) => ({
  id: c.id,
  alert_id: c.alert_id,
  subject: c.subject,
  score: c.score,
  level: c.level,
  status: c.status,
  decision: c.decision,
  updated_at: c.updated_at,
})

export function mockGetCases() {
  const list = Object.values(CASE_BY_ALERT)
    .map((id) => ensureCase(id))
    .filter(Boolean)
    .map(summarize)
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
  return delay(list)
}

// Returns null when the case does not exist.
export function mockGetCase(id) {
  const c = ensureCase(id)
  return delay(c ? structuredClone(c) : null)
}

// POST /cases/{id}/decision. FRAUD and FALSE_POSITIVE close the case;
// NEEDS_MORE_INFORMATION keeps it open.
export function mockSubmitDecision(id, decision) {
  const c = ensureCase(id)
  if (!c) return Promise.reject(new Error('Case not found'))
  if (!DECISIONS.includes(decision)) return Promise.reject(new Error('Unknown decision'))
  if (c.status === 'CLOSED') return Promise.reject(new Error('Case is already closed'))

  const now = new Date().toISOString()
  c.decision = decision
  c.decided_by = MOCK_ANALYST
  c.decided_at = now
  c.updated_at = now
  c.events.push({ time: now, ...DECISION_EVENT[decision] })
  if (decision !== 'NEEDS_MORE_INFORMATION') {
    c.status = 'CLOSED'
    const alert = ALERTS.find((a) => a.id === c.alert_id)
    if (alert) alert.status = 'CLOSED'
  }
  return delay(structuredClone(c))
}

// ---------- Relationship graph ----------
export function mockGetGraph(phone) {
  const alert = ALERTS.find((a) => a.recipient_phone === phone)
  if (!alert) return delay(null)
  const d = buildDetail(alert)

  const subject = {
    id: `acct-${phone}`,
    kind: 'subject',
    phone,
    level: d.level,
    score: d.score,
    report_count: d.reports_total,
    last_activity: alert.created_at,
  }

  const related = d.related_accounts.map((r) => {
    const other = ALERTS.find((a) => a.recipient_phone === r.phone)
    return {
      relation: r.relation,
      node: {
        id: `acct-${r.phone}`,
        kind: 'account',
        phone: r.phone,
        level: other ? other.level : r.level,
        score: other ? other.score : null,
        report_count: other ? buildDetail(other).reports_total : 0,
        last_activity: other ? other.created_at : null,
      },
    }
  })

  const reports = d.reports.map((r) => ({
    id: `report-${r.id}`,
    kind: 'report',
    report_id: r.id,
    created_at: r.created_at,
    scam_type: r.scam_type,
    summary: r.summary,
  }))

  return delay({
    phone,
    reports_total: d.reports_total,
    nodes: [subject, ...related.map((r) => r.node), ...reports],
    edges: [
      ...related.map((r) => ({ id: `edge-${r.node.id}`, source: subject.id, target: r.node.id, type: r.relation })),
      ...reports.map((r) => ({ id: `edge-${r.id}`, source: subject.id, target: r.id, type: 'REPORT' })),
    ],
  })
}
// ---------- Payment simulation ----------
let nextTxnId = 884001

// POST /transactions/simulate. No real money moves: it only records the attempt.
export function mockSimulateTransaction(recipient_phone, amount) {
  if (!/^0[79]\d{8}$/.test(recipient_phone) || !(amount > 0)) {
    return Promise.reject(Object.assign(new Error('Invalid payment'), { status: 422 }))
  }
  return delay({
    id: nextTxnId++,
    status: 'SIMULATED',
    recipient_phone,
    amount,
    created_at: new Date().toISOString(),
  })
}
