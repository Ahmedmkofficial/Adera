import { AxiosError } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { SESSION_KEY } from '../auth/constants'
import { UNAUTHORIZED_EVENT } from '../services/events'

// Loads the API layer in "real backend" mode, with the network replaced by `handler`.
async function realApi(handler) {
  vi.resetModules()
  vi.stubEnv('VITE_USE_MOCK', 'false')
  const api = await import('../services/api')
  const { http } = await import('../services/http')
  const seen = []
  http.defaults.adapter = async (config) => {
    seen.push(config)
    return handler(config)
  }
  return { api, seen }
}

const reply = (config, data, status = 200) => ({ data, status, statusText: 'OK', headers: {}, config })
const failWith = (config, status) => {
  throw new AxiosError('Request failed', 'ERR_BAD_RESPONSE', config, null, {
    status,
    data: {},
    headers: {},
    config,
    statusText: '',
  })
}
const b64url = (o) => btoa(JSON.stringify(o)).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')
const jwt = (claims) => `${b64url({ alg: 'HS256' })}.${b64url(claims)}.signature`

function signedIn() {
  sessionStorage.setItem(
    SESSION_KEY,
    JSON.stringify({
      token: 'abc.def.ghi',
      user: { username: 'admin', name: 'Admin', role: 'analyst' },
      expiresAt: Date.now() + 60_000,
    }),
  )
}

describe('demo mode (the default)', () => {
  beforeEach(() => vi.resetModules())

  it('answers from the built-in demo data without any network call', async () => {
    const { checkRisk } = await import('../services/api')
    const result = await checkRisk('0912345678', 5000)
    expect(result).toMatchObject({ score: 75, level: 'CRITICAL', recommendation: 'STOP_AND_VERIFY' })
  })
})

describe('real backend mode', () => {
  it('sends the risk check to POST /risk/check', async () => {
    const answer = { score: 10, level: 'LOW', recommendation: 'ALLOW', reasons: [] }
    const { api, seen } = await realApi((c) => reply(c, answer))
    expect(await api.checkRisk('0911111111', 250)).toEqual(answer)
    expect(seen[0].method).toBe('post')
    expect(seen[0].url).toBe('/risk/check')
    expect(JSON.parse(seen[0].data)).toEqual({ recipient_phone: '0911111111', amount: 250 })
  })

  it('attaches the signed-in token to requests', async () => {
    signedIn()
    const { api, seen } = await realApi((c) => reply(c, []))
    await api.getAlerts()
    expect(seen[0].headers.Authorization).toBe('Bearer abc.def.ghi')
  })

  it('sends no token when nobody is signed in', async () => {
    const { api, seen } = await realApi((c) => reply(c, []))
    await api.getAlerts()
    expect(seen[0].headers.Authorization).toBeUndefined()
  })

  it('requests the implemented dashboard summary endpoint', async () => {
    const summary = { alerts: 2, critical: 1, high: 1, open_cases: 1, reports: 3 }
    const { api, seen } = await realApi((c) => reply(c, summary))

    await expect(api.getDashboardSummary()).resolves.toEqual(summary)
    expect(seen[0].method).toBe('get')
    expect(seen[0].url).toBe('/dashboard/summary')
  })

  it('requests the implemented recipient graph endpoint', async () => {
    const graph = {
      phone: '0912345678',
      reports_total: 0,
      nodes: [{
        id: 'subject-1',
        kind: 'subject',
        phone: '0912345678',
        level: 'LOW',
        score: 0,
        report_count: 0,
        last_activity: null,
      }],
      edges: [],
    }
    const { api, seen } = await realApi((c) => reply(c, graph))

    await expect(api.getGraph('0912345678')).resolves.toEqual(graph)
    expect(seen[0].method).toBe('get')
    expect(seen[0].url).toBe('/recipients/0912345678/graph')
  })

  it('normalizes the recipient summary without inventing unavailable profile details', async () => {
    const summary = {
      phone: '0912345678',
      risk_score: 75,
      risk_level: 'CRITICAL',
      fraud_report_count: 4,
      independent_reporter_count: 3,
      recent_report_count: 2,
      previous_scam_case_count: 1,
      suspicious_relationship_count: 2,
    }
    const { api } = await realApi((c) => reply(c, summary))

    await expect(api.getEntity(summary.phone)).resolves.toMatchObject({
      phone: summary.phone,
      score: 75,
      level: 'CRITICAL',
      recommendation: 'STOP_AND_VERIFY',
      reports_count: 4,
      recent_reports: 2,
      scam_cases: 1,
      suspicious_relationship_count: 2,
    })
    const entity = await api.getEntity(summary.phone)
    expect(entity.reports).toBeUndefined()
    expect(entity.risk_history).toBeUndefined()
  })

  it('normalizes alert list fields and backend status values', async () => {
    const { api } = await realApi((c) =>
      reply(c, [
        {
          id: 12,
          recipient_phone: '0912345678',
          severity: 'HIGH',
          risk_score: 65,
          risk_level: 'HIGH',
          message: 'Recorded alert message',
          status: 'INVESTIGATING',
          created_at: '2026-10-23T12:00:00',
        },
        {
          id: 13,
          recipient_phone: '0912345679',
          severity: 'CRITICAL',
          risk_score: null,
          risk_level: null,
          message: 'Alert without a risk assessment',
          status: 'DISMISSED',
          created_at: '2026-10-23T12:00:00',
        },
      ]),
    )

    await expect(api.getAlerts()).resolves.toMatchObject([
      { id: 12, score: 65, level: 'HIGH', reason: 'Recorded alert message', status: 'IN_CASE' },
      { id: 13, score: null, level: 'CRITICAL', reason: 'Alert without a risk assessment', status: 'CLOSED' },
    ])
  })

  it('normalizes nested alert details into the investigation view shape', async () => {
    const { api } = await realApi((c) => reply(c, {
      alert: {
        id: 12,
        recipient_phone: '0912345678',
        message: 'Recorded alert message',
        severity: 'HIGH',
        status: 'INVESTIGATING',
        created_at: '2026-10-23T12:00:00',
      },
      risk_assessment: { score: 65, level: 'HIGH', recommendation: 'VERIFY' },
      reasons: ['Recorded alert message'],
      reports_total: 1,
      reports: [{ id: 3, created_at: '2026-10-22T12:00:00', scam_type: 'IMPERSONATION', summary: 'Observed report' }],
      transactions: [{ id: 5, created_at: '2026-10-22T11:00:00', counterparty: '0912345000', amount: 500 }],
      related_accounts: [{ phone: '0912345001', relation: 'TRANSACTION', level: 'LOW' }],
      case_id: 8,
    }))

    await expect(api.getAlert(12)).resolves.toMatchObject({
      id: 12,
      score: 65,
      level: 'HIGH',
      status: 'IN_CASE',
      recommendation: 'VERIFY',
      reports_total: 1,
      case_id: 8,
    })
  })

  it('normalizes case list entries while keeping unavailable risk fields unavailable', async () => {
    const { api } = await realApi((c) => reply(c, [
      {
        id: 9,
        title: 'Persisted alert message',
        status: 'INVESTIGATING',
        recipient_phone: '0912345678',
        alert_id: 12,
        score: 65,
        level: 'HIGH',
        decision: 'NEEDS_MORE_INFORMATION',
        created_at: '2026-10-23T12:00:00',
        updated_at: '2026-10-23T12:00:00',
      },
      {
        id: 10,
        title: 'Case without alert',
        status: 'OPEN',
        recipient_phone: '0912345679',
        score: null,
        level: null,
        decision: null,
        created_at: '2026-10-23T12:00:00',
      },
    ]))

    await expect(api.getCases()).resolves.toMatchObject([
      { id: 9, subject: '0912345678', status: 'OPEN', score: 65, level: 'HIGH' },
      { id: 10, subject: '0912345679', status: 'OPEN', score: null, level: null },
    ])
  })

  it('announces an ended session when the server answers 401', async () => {
    signedIn()
    const { api } = await realApi((c) => failWith(c, 401))
    const heard = vi.fn()
    window.addEventListener(UNAUTHORIZED_EVENT, heard)
    await expect(api.getAlerts()).rejects.toBeTruthy()
    window.removeEventListener(UNAUTHORIZED_EVENT, heard)
    expect(heard).toHaveBeenCalledTimes(1)
  })

  it('signs in with POST /auth/login using the backend phone field', async () => {
    const token = jwt({ sub: 'admin', name: 'Admin', role: 'analyst' })
    const { api, seen } = await realApi((c) => reply(c, { access_token: token }))
    await api.login('admin', 'secret-pass')
    expect(seen[0].url).toBe('/auth/login')
    expect(JSON.parse(seen[0].data)).toEqual({ phone: 'admin', password: 'secret-pass' })
  })

  it('still accepts a backend that sends "phone" in the user object', async () => {
    const token = jwt({ exp: Math.floor(Date.now() / 1000) + 600 })
    const { api } = await realApi((c) =>
      reply(c, { access_token: token, user: { phone: '0911000001', name: 'Hana', role: 'customer' } }),
    )
    const session = await api.login('0911000001', 'pw-pw-pw-1')
    expect(session.user.username).toBe('0911000001')
  })

  it('does not treat a wrong password as an ended session', async () => {
    const { api } = await realApi((c) => failWith(c, 401))
    const heard = vi.fn()
    window.addEventListener(UNAUTHORIZED_EVENT, heard)
    await expect(api.login('0911000001', 'wrong')).rejects.toBeTruthy()
    window.removeEventListener(UNAUTHORIZED_EVENT, heard)
    expect(heard).not.toHaveBeenCalled()
  })

  it('turns "404 not found" into null, but still reports other failures', async () => {
    const missing = await realApi((c) => failWith(c, 404))
    expect(await missing.api.getAlert(1)).toBeNull()
    const broken = await realApi((c) => failWith(c, 500))
    await expect(broken.api.getAlert(1)).rejects.toBeTruthy()
  })

  it('keeps unusual characters out of the URL path', async () => {
    const { api, seen } = await realApi((c) => reply(c, null))
    await api.getEntity('09/12 ../x')
    expect(seen[0].url).toBe('/recipients/09%2F12%20..%2Fx')
  })

  it('reads name, role and expiry from the token when the response has no user object', async () => {
    const exp = Math.floor(Date.now() / 1000) + 600
    const token = jwt({ sub: 'selam', name: 'Selam', role: 'analyst', exp })
    const { api } = await realApi((c) => reply(c, { access_token: token, token_type: 'bearer' }))
    const session = await api.login('selam', 'pw-pw-pw-1')
    expect(session.user).toEqual({ username: 'selam', name: 'Selam', role: 'analyst' })
    expect(session.expiresAt).toBe(exp * 1000)
  })

  it('refuses a sign-in response with an unknown role', async () => {
    const token = jwt({ sub: 'selam', role: 'superuser' })
    const { api } = await realApi((c) => reply(c, { access_token: token }))
    await expect(api.login('selam', 'pw-pw-pw-1')).rejects.toThrow('Unexpected sign-in response')
  })

  it('records a decision with POST /cases/{id}/decision', async () => {
    const { api, seen } = await realApi((c) => {
      if (c.url === '/cases/7/decision') return reply(c, { id: 7, decision: 'FRAUD', status: 'RESOLVED' })
      return reply(c, {
        case: { id: 7, alert_id: 3, recipient_phone: '0912345678', status: 'RESOLVED', decision: 'FRAUD', created_at: '2026-10-23T12:00:00' },
        alert: { id: 3, recipient_phone: '0912345678', severity: 'HIGH' },
        risk_assessment: { score: 65, level: 'HIGH', recommendation: 'VERIFY' },
        events: [],
        evidence: { reports: 0, recent: 0, scam_cases: 0, related_accounts: 0 },
        payment: null,
      })
    })
    const updated = await api.submitDecision(7, 'FRAUD')
    expect(seen[0].url).toBe('/cases/7/decision')
    expect(JSON.parse(seen[0].data)).toEqual({ decision: 'FRAUD' })
    expect(seen[1].url).toBe('/cases/7')
    expect(updated.status).toBe('CLOSED')
  })

  it('opens a case with the selected alert message as title and description', async () => {
    const { api, seen } = await realApi((c) => reply(c, { id: 9 }))
    await api.createCase({ id: 1042, message: 'High-risk recipient requires review.' })
    expect(seen[0].url).toBe('/cases')
    expect(JSON.parse(seen[0].data)).toEqual({
      alert_id: 1042,
      title: 'High-risk recipient requires review.',
      description: 'High-risk recipient requires review.',
    })
  })

  it('refuses case creation when the selected alert has no recorded message', async () => {
    const { api, seen } = await realApi((c) => reply(c, { id: 9 }))
    await expect(api.createCase({ id: 1042 })).rejects.toThrow('no recorded message')
    expect(seen).toHaveLength(0)
  })

  it('updates alert status using the backend status vocabulary', async () => {
    const { api, seen } = await realApi((c) =>
      reply(c, { id: 9, recipient_phone: '0912345678', severity: 'HIGH', status: 'INVESTIGATING' }),
    )
    await expect(api.updateAlertStatus(9, 'IN_CASE')).resolves.toMatchObject({ status: 'IN_CASE' })
    expect(seen[0].method).toBe('patch')
    expect(JSON.parse(seen[0].data)).toEqual({ status: 'INVESTIGATING' })
  })
})
