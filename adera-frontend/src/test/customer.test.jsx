import { act, fireEvent, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { CUSTOMER, renderApp, signInAs } from './helpers'

async function check(user, phone, amount = '5000') {
  await user.type(screen.getByLabelText('Amount in Ethiopian birr'), amount)
  await user.type(screen.getByLabelText('Recipient phone'), phone)
  await user.click(screen.getByRole('button', { name: 'Check recipient' }))
  return screen.findByRole('dialog')
}

describe('send money', () => {
  it('keeps the check button off until the amount and phone number are valid', async () => {
    const user = userEvent.setup()
    signInAs(CUSTOMER)
    renderApp('/')
    const button = await screen.findByRole('button', { name: 'Check recipient' })
    expect(button).toBeDisabled()
    await user.type(screen.getByLabelText('Amount in Ethiopian birr'), '5000')
    expect(screen.getByLabelText('Amount in Ethiopian birr')).toHaveValue('5,000')
    await user.type(screen.getByLabelText('Recipient phone'), '0912345678')
    expect(button).toBeEnabled()
  })

  it('shows a critical warning with the reasons from the risk check', async () => {
    const user = userEvent.setup()
    signInAs(CUSTOMER)
    renderApp('/')
    await screen.findByRole('heading', { name: 'Send' })
    const sheet = await check(user, '0912345678')
    expect(within(sheet).getByText('Critical')).toBeInTheDocument()
    expect(within(sheet).getByText('Stop and verify')).toBeInTheDocument()
    expect(within(sheet).getAllByRole('listitem')).toHaveLength(4)
    expect(within(sheet).getByRole('button', { name: 'Cancel payment' })).toBeInTheDocument()
  })

  it('closes the warning with Escape', async () => {
    const user = userEvent.setup()
    signInAs(CUSTOMER)
    renderApp('/')
    await screen.findByRole('heading', { name: 'Send' })
    await check(user, '0912345678')
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('cancels a risky payment without sending anything', async () => {
    const user = userEvent.setup()
    signInAs(CUSTOMER)
    renderApp('/')
    await screen.findByRole('heading', { name: 'Send' })
    await check(user, '0912345678')
    await user.click(screen.getByRole('button', { name: 'Cancel payment' }))
    expect(await screen.findByRole('heading', { name: 'Payment cancelled' })).toBeInTheDocument()
    expect(screen.queryByText('Reference')).not.toBeInTheDocument()
  })

  it('sends a low-risk payment and shows a receipt with a reference', async () => {
    const user = userEvent.setup()
    signInAs(CUSTOMER)
    renderApp('/')
    await screen.findByRole('heading', { name: 'Send' })
    const sheet = await check(user, '0933333333', '750')
    expect(within(sheet).getByText('Low')).toBeInTheDocument()
    await user.click(within(sheet).getByRole('button', { name: 'Continue' }))
    expect(await screen.findByRole('heading', { name: 'Payment sent' })).toBeInTheDocument()
    expect(screen.getByText(/^TXN-8840/)).toBeInTheDocument()
    expect(screen.getByText('750 ETB')).toBeInTheDocument()
    expect(screen.getByText('Risk check').nextSibling).toHaveTextContent('Low')
  })

  it('needs a real press-and-hold to send past a critical warning', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    signInAs(CUSTOMER)
    renderApp('/')
    await screen.findByRole('heading', { name: 'Send' })
    await check(user, '0912345678')
    const hold = screen.getByRole('button', { name: 'Hold to send anyway' })

    // let go too early: nothing happens
    fireEvent.pointerDown(hold)
    await act(async () => {
      vi.advanceTimersByTime(800)
    })
    fireEvent.pointerUp(hold)
    await act(async () => {
      vi.advanceTimersByTime(2000)
    })
    expect(screen.queryByRole('heading', { name: 'Payment sent' })).not.toBeInTheDocument()

    // hold long enough: the payment is recorded
    fireEvent.pointerDown(hold)
    await act(async () => {
      vi.advanceTimersByTime(1600)
    })
    expect(await screen.findByRole('heading', { name: 'Payment sent' })).toBeInTheDocument()
  })
})

describe('reporting', () => {
  it('checks the form, then thanks the customer', async () => {
    const user = userEvent.setup()
    signInAs(CUSTOMER)
    renderApp('/')
    await user.click(await screen.findByRole('button', { name: 'Report suspicious activity' }))
    const submit = await screen.findByRole('button', { name: 'Submit report' })

    await user.click(submit)
    expect(screen.getByRole('alert')).toHaveTextContent('10-digit phone number')

    await user.type(screen.getByLabelText('Recipient phone'), '0912345678')
    await user.click(submit)
    expect(screen.getByRole('alert')).toHaveTextContent('Choose the type of activity')

    await user.click(screen.getByLabelText('Impersonation'))
    await user.type(screen.getByLabelText('What happened?'), 'short')
    await user.click(submit)
    expect(screen.getByRole('alert')).toHaveTextContent('at least 10 characters')

    await user.clear(screen.getByLabelText('What happened?'))
    await user.type(screen.getByLabelText('What happened?'), 'They pretended to be my cousin and asked for money.')
    await user.click(submit)
    expect(await screen.findByRole('heading', { name: 'Report submitted' })).toBeInTheDocument()
  })

  it('sends people with an unknown receipt address back to the payment screen', async () => {
    signInAs(CUSTOMER)
    renderApp('/confirmation/banana')
    expect(await screen.findByRole('heading', { name: 'Send' })).toBeInTheDocument()
  })
})
