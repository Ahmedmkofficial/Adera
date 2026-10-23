import { screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ANALYST, CUSTOMER, renderApp, signInAs } from './helpers'

// The product should read as a finished product: no "prototype", "demo", "synthetic",
// "mock" or version labels anywhere a person can see them.
const BANNED = /prototype|synthetic|demo|mock|v0\.\d|work in progress/i

async function textOf(path, user) {
  if (user) signInAs(user)
  renderApp(path)
  await waitFor(() => expect(document.querySelector('h1, h2')).not.toBeNull())
  await waitFor(() => expect(document.body.textContent).not.toMatch(/Loading/))
  return document.body.textContent
}

describe('wording', () => {
  it.each(['/login', '/register'])('%s has no prototype wording', async (path) => {
    expect(await textOf(path)).not.toMatch(BANNED)
  })

  it.each(['/', '/report'])('%s (customer) has no prototype wording', async (path) => {
    expect(await textOf(path, CUSTOMER)).not.toMatch(BANNED)
  })

  it.each([
    '/admin',
    '/admin/alerts',
    '/admin/alerts/1042',
    '/admin/entities',
    '/admin/entity/0912345678',
    '/admin/cases',
    '/admin/cases/1018',
  ])('%s (analyst) has no prototype wording', async (path) => {
    expect(await textOf(path, ANALYST)).not.toMatch(BANNED)
  })

  it('has no version label in the sidebar', async () => {
    await textOf('/admin', ANALYST)
    expect(screen.queryByText(/v0\.1/)).not.toBeInTheDocument()
  })
})

describe('logo', () => {
  it('shows the Adera logo on the customer pages and in the analyst sidebar', async () => {
    await textOf('/', CUSTOMER)
    expect(screen.getByRole('img', { name: 'Adera' })).toBeInTheDocument()
  })

  it('shows one large logo above the wordmark on the sign-in page', async () => {
    await textOf('/login')
    expect(document.querySelectorAll('.cu-wordmark-mark')).toHaveLength(1)
  })
})
