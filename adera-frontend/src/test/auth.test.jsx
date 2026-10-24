import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { IDLE_MS, SESSION_KEY } from '../auth/constants'
import { ANALYST, CUSTOMER, renderApp, signInAs } from './helpers'

describe('who can see what', () => {
  it('sends a signed-out visitor to the sign-in page', async () => {
    renderApp('/admin/alerts')
    expect(await screen.findByRole('button', { name: 'Sign in to analyst dashboard' })).toBeInTheDocument()
  })

  it('provides a separate analyst login route and a link back to user login', async () => {
    renderApp('/analyst/login')
    expect(await screen.findByRole('heading', { name: 'Analyst sign in' })).toBeInTheDocument()
    expect(screen.getByLabelText('Staff username or phone number')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'User sign in' })).toHaveAttribute('href', '/login')
  })

  it('redirects a signed-in customer away from the analyst login URL', async () => {
    signInAs(CUSTOMER)
    renderApp('/analyst/login')
    expect(await screen.findByRole('heading', { name: 'Send' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Overview' })).not.toBeInTheDocument()
  })

  it('keeps customers out of the analyst area', async () => {
    signInAs(CUSTOMER)
    renderApp('/admin')
    expect(await screen.findByRole('heading', { name: 'No access' })).toBeInTheDocument()
    expect(screen.queryByText('Overview')).not.toBeInTheDocument()
  })

  it('lets analysts in', async () => {
    signInAs(ANALYST)
    renderApp('/admin')
    expect(await screen.findByRole('heading', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByText('Admin')).toBeInTheDocument()
  })

  it('lets a signed-in customer use the payment screen', async () => {
    signInAs(CUSTOMER)
    renderApp('/')
    expect(await screen.findByRole('heading', { name: 'Send' })).toBeInTheDocument()
  })

  it('ignores a session whose role was edited by hand', async () => {
    signInAs({ ...ANALYST, role: 'root' })
    renderApp('/admin')
    expect(await screen.findByRole('button', { name: 'Sign in to analyst dashboard' })).toBeInTheDocument()
    expect(sessionStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('ignores an expired session', async () => {
    signInAs(ANALYST, { expiresAt: Date.now() - 1000 })
    renderApp('/admin')
    expect(await screen.findByRole('button', { name: 'Sign in to analyst dashboard' })).toBeInTheDocument()
  })
})

async function signInWith(user, identifier, password) {
  await user.type(screen.getByLabelText('Phone number'), identifier)
  await user.type(screen.getByLabelText('Password'), password)
  await user.click(screen.getByRole('button', { name: 'Sign in' }))
}

describe('signing in and out', () => {
  it('rejects a wrong password with one generic message', async () => {
    const user = userEvent.setup()
    renderApp('/login')
    await signInWith(user, '0911000001', 'not-the-password')
    expect(await screen.findByRole('alert')).toHaveTextContent('Those sign-in details are incorrect.')
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('gives the same message for a phone number that does not exist', async () => {
    const user = userEvent.setup()
    renderApp('/login')
    await signInWith(user, '0911999999', 'whatever-pass')
    expect(await screen.findByRole('alert')).toHaveTextContent('Those sign-in details are incorrect.')
  })

  it('validates the form before asking the server', async () => {
    const user = userEvent.setup()
    renderApp('/login')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(screen.getByRole('alert')).toHaveTextContent('10-digit phone number')
    await user.type(screen.getByLabelText('Phone number'), '0912')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(screen.getByRole('alert')).toHaveTextContent('10-digit phone number')
    await user.clear(screen.getByLabelText('Phone number'))
    await user.type(screen.getByLabelText('Phone number'), '0911000001')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Enter your password.')
  })

  it('signs in the admin with the username "admin" and takes them to the analyst area', async () => {
    const user = userEvent.setup()
    renderApp('/analyst/login')
    await user.type(screen.getByLabelText('Staff username or phone number'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'admin')
    await user.click(screen.getByRole('button', { name: 'Sign in to analyst dashboard' }))
    expect(await screen.findByRole('heading', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByText('Admin')).toBeInTheDocument()
  })

  it('signs in an analyst from the dedicated route', async () => {
    const user = userEvent.setup()
    renderApp('/analyst/login')
    await user.type(screen.getByLabelText('Staff username or phone number'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'admin')
    await user.click(screen.getByRole('button', { name: 'Sign in to analyst dashboard' }))
    expect(await screen.findByRole('heading', { name: 'Overview' })).toBeInTheDocument()
  })

  it('does not establish an analyst session for a regular user account', async () => {
    const user = userEvent.setup()
    renderApp('/analyst/login')
    await user.type(screen.getByLabelText('Staff username or phone number'), '0911000001')
    await user.type(screen.getByLabelText('Password'), 'demo-customer-1')
    await user.click(screen.getByRole('button', { name: 'Sign in to analyst dashboard' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('regular user access')
    expect(sessionStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('keeps usernames on the dedicated analyst login route', async () => {
    const user = userEvent.setup()
    renderApp('/login')
    await signInWith(user, 'admin', 'admin')
    expect(await screen.findByRole('alert')).toHaveTextContent('10-digit phone number')
    expect(sessionStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('does not mind capital letters in a username', async () => {
    const user = userEvent.setup()
    renderApp('/analyst/login')
    await user.type(screen.getByLabelText('Staff username or phone number'), 'ADMIN')
    await user.type(screen.getByLabelText('Password'), 'admin')
    await user.click(screen.getByRole('button', { name: 'Sign in to analyst dashboard' }))
    expect(await screen.findByRole('heading', { name: 'Overview' })).toBeInTheDocument()
  })

  it('signs a customer in with their phone number and shows the payment screen', async () => {
    const user = userEvent.setup()
    renderApp('/login')
    await signInWith(user, '0911000001', 'demo-customer-1')
    expect(await screen.findByRole('heading', { name: 'Send' })).toBeInTheDocument()
  })

  it('returns to the page the visitor first asked for', async () => {
    const user = userEvent.setup()
    renderApp('/admin/cases')
    await user.type(screen.getByLabelText('Staff username or phone number'), 'admin')
    await user.type(screen.getByLabelText('Password'), 'admin')
    await user.click(screen.getByRole('button', { name: 'Sign in to analyst dashboard' }))
    expect(await screen.findByRole('heading', { name: 'Cases' })).toBeInTheDocument()
  })

  it('signs out and forgets the session', async () => {
    const user = userEvent.setup()
    signInAs(ANALYST)
    renderApp('/admin')
    await user.click(await screen.findByRole('button', { name: 'Sign out' }))
    expect(await screen.findByRole('button', { name: 'Sign in to analyst dashboard' })).toBeInTheDocument()
    expect(sessionStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('signs out after a quiet spell and says why', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    signInAs(CUSTOMER)
    renderApp('/')
    expect(await screen.findByRole('heading', { name: 'Send' })).toBeInTheDocument()
    await act(async () => {
      vi.advanceTimersByTime(IDLE_MS + 1000)
    })
    expect(await screen.findByRole('status')).toHaveTextContent('15 minutes of inactivity')
  })
})

describe('creating an account', () => {
  it('creates a customer account and asks them to sign in', async () => {
    const user = userEvent.setup()
    renderApp('/register')
    await user.type(screen.getByLabelText('Phone number'), '0922123456')
    await user.type(screen.getByLabelText('Full name'), 'Sara Bekele')
    await user.type(screen.getByLabelText('Password'), 'a-long-password')
    await user.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Account created')
  })

  it('refuses a phone number that already has an account', async () => {
    const user = userEvent.setup()
    renderApp('/register')
    await user.type(screen.getByLabelText('Phone number'), '0911000001')
    await user.type(screen.getByLabelText('Full name'), 'Someone Else')
    await user.type(screen.getByLabelText('Password'), 'a-long-password')
    await user.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('already exists')
  })

  it('needs a password of at least 8 characters', async () => {
    const user = userEvent.setup()
    renderApp('/register')
    await user.type(screen.getByLabelText('Phone number'), '0922123457')
    await user.type(screen.getByLabelText('Full name'), 'Sara Bekele')
    await user.type(screen.getByLabelText('Password'), 'short')
    await user.click(screen.getByRole('button', { name: 'Create account' }))
    expect(screen.getByRole('alert')).toHaveTextContent('at least 8 characters')
  })
})
