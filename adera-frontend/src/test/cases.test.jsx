import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ANALYST, renderApp, signInAs } from './helpers'

describe('cases', () => {
  it('lists the cases and filters them by status', async () => {
    const user = userEvent.setup()
    signInAs(ANALYST)
    renderApp('/admin/cases')
    expect(await screen.findByText('#1018')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /#\d+/ })).toHaveLength(4)
    await user.click(screen.getByRole('button', { name: 'Closed' }))
    expect(screen.getAllByRole('link', { name: /#\d+/ })).toHaveLength(2)
  })

  it('keeps a case open while more information is needed', async () => {
    signInAs(ANALYST)
    renderApp('/admin/cases/1018')
    expect(await screen.findByText(/More information was requested/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Needs more information/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mark as fraud' })).toBeInTheDocument()
  })

  it('asks for confirmation, then closes the case for good', async () => {
    const user = userEvent.setup()
    signInAs(ANALYST)
    renderApp('/admin/cases/1009')
    await user.click(await screen.findByRole('button', { name: 'Mark as fraud' }))
    expect(screen.getByText('Record this case as fraud?')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.getByRole('button', { name: 'Mark as fraud' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Mark as fraud' }))
    await user.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(await screen.findByRole('heading', { name: 'Decision recorded' })).toBeInTheDocument()
    expect(screen.getByText(/FRAUD · RECORDED/)).toBeInTheDocument()
    expect(screen.getByText('Recorded by').nextSibling).toHaveTextContent('Admin')
    expect(screen.queryByRole('button', { name: 'Mark as fraud' })).not.toBeInTheDocument()
    await waitFor(() => expect(document.activeElement).toHaveTextContent('Decision recorded'))
  })

  it('shows a closed case as read-only', async () => {
    signInAs(ANALYST)
    renderApp('/admin/cases/998')
    expect(await screen.findByRole('heading', { name: 'Decision recorded' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /fraud|false positive|more information/i })).not.toBeInTheDocument()
  })

  it('says so when a case does not exist', async () => {
    signInAs(ANALYST)
    renderApp('/admin/cases/5555')
    expect(await screen.findByRole('heading', { name: 'Case not found' })).toBeInTheDocument()
  })
})
