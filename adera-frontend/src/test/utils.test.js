import { describe, expect, it } from 'vitest'
import { canVisit, destinationFor, homeFor } from '../auth/access'
import { SESSION_KEY } from '../auth/constants'
import { decodeJwtPayload, loadSession } from '../auth/session'
import { formatAlertId, formatCaseId, formatTxnId, timeAgo } from '../utils/format'
import { CENTER_Y, NODE_W, layoutGraph } from '../utils/graphLayout'
import { RECOMMENDATION_LABEL, levelClass, levelLabel } from '../utils/risk'

describe('risk wording', () => {
  it('has a label for every recommendation the Risk Engine can return', () => {
    for (const key of ['ALLOW', 'REVIEW', 'VERIFY', 'STOP_AND_VERIFY']) {
      expect(RECOMMENDATION_LABEL[key]).toBeTruthy()
    }
  })
  it('formats levels', () => {
    expect(levelLabel('CRITICAL')).toBe('Critical')
    expect(levelClass('MODERATE')).toBe('lvl-moderate')
  })
})

describe('formatting', () => {
  it('formats ids the way the screens show them', () => {
    expect(formatAlertId(1042)).toBe('ALR-1042')
    expect(formatCaseId(1021)).toBe('#1021')
    expect(formatTxnId(884001)).toBe('TXN-884001')
  })
  it('describes how long ago something happened', () => {
    const ago = (m) => new Date(Date.now() - m * 60000).toISOString()
    expect(timeAgo(ago(0))).toBe('just now')
    expect(timeAgo(ago(5))).toBe('5m ago')
    expect(timeAgo(ago(125))).toBe('2h ago')
    expect(timeAgo(ago(60 * 24 + 5))).toBe('Yesterday')
    expect(timeAgo(ago(60 * 24 * 3))).toBe('3d ago')
  })
})

describe('access rules', () => {
  it('starts each role in the right place', () => {
    expect(homeFor('analyst')).toBe('/admin')
    expect(homeFor('customer')).toBe('/')
  })
  it('only lets analysts into /admin', () => {
    expect(canVisit('analyst', '/admin/cases')).toBe(true)
    expect(canVisit('customer', '/admin/cases')).toBe(false)
    expect(canVisit('customer', '/report')).toBe(true)
  })
  it('never redirects somewhere the role is not allowed (or somewhere odd)', () => {
    expect(destinationFor('customer', '/admin')).toBe('/')
    expect(destinationFor('analyst', '/admin/alerts')).toBe('/admin/alerts')
    expect(destinationFor('analyst', undefined)).toBe('/admin')
    // opening the plain address first must not strand an analyst on the customer page
    expect(destinationFor('analyst', '/')).toBe('/admin')
    expect(destinationFor('analyst', '/report')).toBe('/admin')
    expect(destinationFor('customer', '/report')).toBe('/report')
    expect(destinationFor('customer', { not: 'a path' })).toBe('/')
  })
})

describe('session storage', () => {
  it('ignores damaged data', () => {
    sessionStorage.setItem(SESSION_KEY, '{not json')
    expect(loadSession()).toBeNull()
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ token: '', user: {} }))
    expect(loadSession()).toBeNull()
  })
  it('reads token claims, and survives rubbish', () => {
    const payload = btoa(JSON.stringify({ role: 'analyst', name: 'Selam' })).replace(/=+$/, '')
    expect(decodeJwtPayload(`x.${payload}.y`)).toEqual({ role: 'analyst', name: 'Selam' })
    expect(decodeJwtPayload('not-a-token')).toBeNull()
    expect(decodeJwtPayload(undefined)).toBeNull()
  })
})

describe('graph layout', () => {
  const data = {
    nodes: [
      { id: 's', kind: 'subject' },
      { id: 'a1', kind: 'account' },
      { id: 'a2', kind: 'account' },
      { id: 'r1', kind: 'report' },
      { id: 'r2', kind: 'report' },
    ],
    edges: [
      { id: 'e1', source: 's', target: 'a1', type: 'SHARED_PHONE' },
      { id: 'e2', source: 's', target: 'r1', type: 'REPORT' },
    ],
  }
  const { nodes, edges } = layoutGraph(data)
  const centre = (id) => {
    const n = nodes.find((x) => x.id === id)
    return { x: n.position.x + NODE_W / 2, y: n.position.y + CENTER_Y[n.type] }
  }

  it('puts the recipient at the middle, accounts either side, reports below', () => {
    expect(centre('s')).toEqual({ x: 0, y: 0 })
    expect(centre('a1')).toEqual({ x: 340, y: 0 })
    expect(centre('a2')).toEqual({ x: -340, y: 0 })
    expect(centre('r1').y).toBeGreaterThan(0)
    expect(centre('r1').x).toBeLessThan(centre('r2').x)
  })
  it('labels relationship lines but leaves report lines plain', () => {
    expect(edges.find((e) => e.id === 'e1').label).toBe('SHARED_PHONE')
    expect(edges.find((e) => e.id === 'e2').label).toBeUndefined()
  })
  it('copes with a recipient that has no connections', () => {
    expect(layoutGraph({ nodes: [{ id: 's', kind: 'subject' }], edges: [] }).nodes).toHaveLength(1)
  })
})
