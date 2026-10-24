// Every call the app makes to the backend goes through this file.
// With VITE_USE_MOCK unset (the default) it answers from src/mock. With
// VITE_USE_MOCK=false it calls the real FastAPI backend using the contract in
// docs/API_CONTRACT.md. Pages never know the difference.
import { decodeJwtPayload } from '../auth/session'
import { ROLES } from '../auth/constants'
import { PHONE_RE } from '../auth/identifier'
import {
  mockCheckRisk,
  mockCreateCase,
  mockGetAlert,
  mockGetAlerts,
  mockGetCase,
  mockGetCases,
  mockGetDashboardSummary,
  mockGetEntity,
  mockGetGraph,
  mockSimulateTransaction,
  mockSubmitDecision,
  mockSubmitReport,
  mockUpdateAlertStatus,
} from '../mock/mockData'
import { mockLogin, mockRegister } from '../mock/mockAuth'
import { USE_MOCK } from './config'
import { http } from './http'

// The HTTP status behind an error, from Axios or from the mock.
export const statusOf = (error) => error?.response?.status ?? error?.status

const body = (request) => request.then((response) => response.data)

// For "get one thing": a 404 means "not there", which the pages show as "not found".
const bodyOrNull = (request) =>
  request.then(
    (response) => response.data,
    (error) => (statusOf(error) === 404 ? null : Promise.reject(error)),
  )

const part = (value) => encodeURIComponent(String(value)) // safe inside a URL path
const RECOMMENDATION_BY_LEVEL = {
  LOW: 'ALLOW',
  MODERATE: 'REVIEW',
  HIGH: 'VERIFY',
  CRITICAL: 'STOP_AND_VERIFY',
}

function normalizeStatus(status) {
  if (status === 'INVESTIGATING') return 'IN_CASE'
  if (status === 'RESOLVED' || status === 'DISMISSED') return 'CLOSED'
  return status
}

function normalizeAlert(data) {
  const alert = data?.alert ?? data
  const risk = data?.risk_assessment
  const level = risk?.level ?? data?.risk_level ?? data?.level ?? alert?.severity
  return {
    ...alert,
    id: alert?.id ?? data?.id,
    recipient_phone: alert?.recipient_phone ?? data?.recipient_phone,
    score: risk?.score ?? data?.risk_score ?? data?.score ?? null,
    level,
    reason: data?.reason ?? alert?.message ?? data?.message ?? '',
    status: normalizeStatus(alert?.status ?? data?.status),
    recommendation:
      risk?.recommendation ??
      data?.recommendation ??
      RECOMMENDATION_BY_LEVEL[level],
    reasons: data?.reasons ?? (alert?.message ? [alert.message] : []),
    transactions: data?.transactions ?? [],
    reports: data?.reports ?? [],
    reports_total: data?.reports_total ?? 0,
    related_accounts: data?.related_accounts ?? [],
    case_id: data?.case_id ?? null,
  }
}

function normalizeEntity(data) {
  if (!data) return null
  const level = data.level ?? data.risk_level
  return {
    ...data,
    score: data.score ?? data.risk_score,
    level,
    recommendation: data.recommendation ?? RECOMMENDATION_BY_LEVEL[level],
    reports_count: data.reports_count ?? data.fraud_report_count,
    recent_reports: data.recent_reports ?? data.recent_report_count,
    scam_cases: data.scam_cases ?? data.previous_scam_case_count,
    reasons: data.reasons,
  }
}

function normalizeCaseStatus(status) {
  if (status === 'INVESTIGATING') return 'OPEN'
  if (status === 'RESOLVED' || status === 'CLOSED') return 'CLOSED'
  return status
}

function normalizeCase(data) {
  if (!data?.case) {
    return { ...data, status: normalizeCaseStatus(data?.status) }
  }
  const record = data.case
  const risk = data.risk_assessment
  const alert = data.alert
  const level = risk?.level ?? alert?.severity ?? data.level
  const transactions = data.relevant_transactions ?? []
  return {
    ...data,
    id: record.id,
    alert_id: record.alert_id,
    subject: record.recipient_phone,
    score: risk?.score ?? data.score ?? null,
    level,
    recommendation:
      risk?.recommendation ??
      data.recommendation ??
      RECOMMENDATION_BY_LEVEL[level],
    status: normalizeCaseStatus(record.status),
    decision: record.decision,
    decided_by: data.decided_by ?? null,
    decided_at: data.decided_at ?? null,
    created_at: record.created_at,
    updated_at: data.updated_at ?? record.created_at,
    events: data.events ?? [],
    evidence: data.evidence ?? {
      reports: data.fraud_reports?.length ?? 0,
      recent: 0,
      scam_cases: 0,
      related_accounts: 0,
    },
    payment: data.payment ?? (transactions[0]
      ? {
          amount: transactions[0].amount,
          txn_id: transactions[0].id,
          created_at: transactions[0].created_at,
        }
      : null),
  }
}

function normalizeRole(role) {
  const value = String(role ?? '').trim().toLowerCase()
  if (value === 'user' || value === 'customer') return 'customer'
  if (value === 'analyst' || value === 'admin') return 'analyst'
  return value
}

// ---------- sign in ----------
function toSession(data) {
  const token = data?.access_token
  const claims = decodeJwtPayload(token) ?? {}
  const user = data?.user ?? { username: claims.sub, name: claims.name, role: claims.role }
  const username = user?.username ?? user?.phone ?? claims.sub
  const role = normalizeRole(user?.role ?? claims.role)
  if (typeof token !== 'string' || !username || !ROLES.includes(role)) {
    throw new Error('Unexpected sign-in response')
  }
  return {
    token,
    user: { username: String(username), name: String(user.name ?? username), role },
    expiresAt: claims.exp ? claims.exp * 1000 : undefined,
  }
}

export async function login(username, password) {
  const identifier = PHONE_RE.test(username)
    ? { phone: username }
    : { username }
  const data = USE_MOCK
    ? await mockLogin(username, password)
    : await body(http.post('/auth/login', { ...identifier, password }))
  return toSession(data)
}

export async function register({ phone, name, password }) {
  return USE_MOCK ? mockRegister({ phone, name, password }) : body(http.post('/auth/register', { phone, name, password }))
}

// ---------- customer ----------
export async function checkRisk(recipient_phone, amount) {
  return USE_MOCK ? mockCheckRisk(recipient_phone, amount) : body(http.post('/risk/check', { recipient_phone, amount }))
}

export async function simulateTransaction(recipient_phone, amount) {
  return USE_MOCK
    ? mockSimulateTransaction(recipient_phone, amount)
    : body(http.post('/transactions/simulate', { recipient_phone, amount }))
}

export async function submitReport(report) {
  return USE_MOCK ? mockSubmitReport(report) : body(http.post('/reports', report))
}

// ---------- analyst ----------
export async function getDashboardSummary() {
  return USE_MOCK ? mockGetDashboardSummary() : body(http.get('/dashboard/summary'))
}

export async function getAlerts() {
  const alerts = USE_MOCK ? await mockGetAlerts() : await body(http.get('/alerts'))
  return alerts.map(normalizeAlert)
}

export async function getAlert(id) {
  const alert = USE_MOCK ? await mockGetAlert(id) : await bodyOrNull(http.get(`/alerts/${part(id)}`))
  return alert ? normalizeAlert(alert) : null
}

export async function getEntity(phone) {
  const entity = USE_MOCK ? await mockGetEntity(phone) : await bodyOrNull(http.get(`/recipients/${part(phone)}`))
  return normalizeEntity(entity)
}

export async function getGraph(phone) {
  return USE_MOCK ? mockGetGraph(phone) : bodyOrNull(http.get(`/recipients/${part(phone)}/graph`))
}

export async function getCases() {
  const cases = USE_MOCK ? await mockGetCases() : await body(http.get('/cases'))
  return cases.map((item) => ({
    ...item,
    subject: item.subject ?? item.recipient_phone,
    status: normalizeCaseStatus(item.status),
    updated_at: item.updated_at ?? item.created_at,
  }))
}

export async function getCase(id) {
  const caseData = USE_MOCK ? await mockGetCase(id) : await bodyOrNull(http.get(`/cases/${part(id)}`))
  return caseData ? normalizeCase(caseData) : null
}

export async function createCase(alert) {
  if (USE_MOCK) return mockCreateCase(typeof alert === 'object' ? alert.id : alert)
  const message = alert?.message?.trim()
  if (!message) {
    throw new Error('This alert has no recorded message to use for the case title and description.')
  }
  return body(
    http.post('/cases', {
      alert_id: alert.id,
      title: message,
      description: message,
    }),
  )
}

export async function submitDecision(id, decision) {
  if (USE_MOCK) return mockSubmitDecision(id, decision)
  await body(http.post(`/cases/${part(id)}/decision`, { decision }))
  const updatedCase = await getCase(id)
  if (!updatedCase) throw new Error('The updated case could not be found')
  return updatedCase
}

export async function updateAlertStatus(id, status) {
  if (USE_MOCK) return normalizeAlert(await mockUpdateAlertStatus(id, status))
  const backendStatus = { IN_CASE: 'INVESTIGATING', CLOSED: 'RESOLVED' }[status] ?? status
  const response = await body(http.patch(`/alerts/${part(id)}`, { status: backendStatus }))
  return normalizeAlert(response)
}
