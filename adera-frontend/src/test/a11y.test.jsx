import { screen } from '@testing-library/react'
import axe from 'axe-core'
import { describe, expect, it } from 'vitest'
import { ANALYST, CUSTOMER, renderApp, signInAs } from './helpers'

// Structure checks (labels, roles, names, landmarks). jsdom cannot judge colour
// contrast, so that is checked by hand: see docs/ACCESSIBILITY.md.
async function violations() {
  const result = await axe.run(document.body, { rules: { 'color-contrast': { enabled: false } } })
  return result.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(' | ')}`)
}

describe('accessibility structure', () => {
  it('sign-in page', async () => {
    renderApp('/login')
    await screen.findByRole('button', { name: 'Sign in' })
    expect(await violations()).toEqual([])
  })

  it('send money page', async () => {
    signInAs(CUSTOMER)
    renderApp('/')
    await screen.findByRole('heading', { name: 'Send' })
    expect(await violations()).toEqual([])
  })

  it('dashboard', async () => {
    signInAs(ANALYST)
    renderApp('/admin')
    await screen.findAllByRole('link', { name: /ALR-/ })
    expect(await violations()).toEqual([])
  })

  it('alert investigation', async () => {
    signInAs(ANALYST)
    renderApp('/admin/alerts/1034')
    await screen.findByRole('heading', { name: 'Alert #1034' })
    expect(await violations()).toEqual([])
  })

  it('case page', async () => {
    signInAs(ANALYST)
    renderApp('/admin/cases/1009')
    await screen.findByRole('heading', { name: 'Case #1009' })
    expect(await violations()).toEqual([])
  })
})
