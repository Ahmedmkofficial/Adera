import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ANALYST, renderApp, signInAs } from './helpers'

const alertLinks = () => screen.getAllByRole('link', { name: /ALR-/ })

describe('dashboard and alerts', () => {
  it('shows the summary strip and the recent alerts, and filters them', async () => {
    const user = userEvent.setup()
    signInAs(ANALYST)
    renderApp('/admin')
    await screen.findByRole('heading', { name: 'Overview' })
    const strip = await screen.findByRole('region', { name: 'Operations summary' })
    expect(await within(strip).findByText('137')).toBeInTheDocument()
    expect(await screen.findAllByRole('link', { name: /ALR-/ })).toHaveLength(6)

    await user.click(screen.getByRole('button', { name: 'Critical' }))
    expect(alertLinks()).toHaveLength(2)
    await user.click(screen.getByRole('button', { name: 'Moderate' }))
    expect(alertLinks()).toHaveLength(2)
  })

  it('sorts the alert list by risk', async () => {
    const user = userEvent.setup()
    signInAs(ANALYST)
    renderApp('/admin/alerts')
    await screen.findAllByRole('link', { name: /ALR-/ })
    await user.click(screen.getByRole('button', { name: /Sort by Risk/ }))
    expect(alertLinks()[0]).toHaveTextContent('ALR-1034') // score 85
    await user.click(screen.getByRole('button', { name: /Sort by Risk/ }))
    expect(alertLinks()[0]).toHaveTextContent('ALR-1027') // score 30
  })
})

describe('investigating an alert', () => {
  it('explains why the alert exists', async () => {
    signInAs(ANALYST)
    renderApp('/admin/alerts/1042')
    expect(await screen.findByRole('heading', { name: 'Alert #1042' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /4 risk indicators contribute/ })).toBeInTheDocument()
    expect(screen.getByText('Multiple independent fraud reports')).toBeInTheDocument()
    expect(screen.getByText(/Showing 3 of 7 reports/)).toBeInTheDocument()
  })

  it('says so when an alert does not exist', async () => {
    signInAs(ANALYST)
    renderApp('/admin/alerts/9999')
    expect(await screen.findByRole('heading', { name: 'Alert not found' })).toBeInTheDocument()
  })

  it('opens a case from an alert', async () => {
    const user = userEvent.setup()
    signInAs(ANALYST)
    renderApp('/admin/alerts/1042')
    await user.click(await screen.findByRole('button', { name: 'Open case' }))
    expect(await screen.findByRole('heading', { name: 'Case #1021' })).toBeInTheDocument()
  })
})

describe('entities', () => {
  it('shows a profile and its risk history chart', async () => {
    const user = userEvent.setup()
    signInAs(ANALYST)
    renderApp('/admin/entity/0912345678')
    expect(await screen.findByRole('heading', { name: '0912345678' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Risk history' }))
    expect(screen.getByRole('img', { name: /Risk score moved from/ })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Relationships' }))
    expect(screen.getByRole('link', { name: 'Open full graph →' })).toBeInTheDocument()
  })

  it('says so when there is no record', async () => {
    signInAs(ANALYST)
    renderApp('/admin/entity/0900000000')
    expect(await screen.findByRole('heading', { name: 'No record found' })).toBeInTheDocument()
  })

  it('checks the phone number typed into the lookup', async () => {
    const user = userEvent.setup()
    signInAs(ANALYST)
    renderApp('/admin/entities')
    await user.type(await screen.findByLabelText('Look up a phone number'), '123')
    await user.click(screen.getByRole('button', { name: 'Open profile' }))
    expect(screen.getByRole('alert')).toHaveTextContent('10-digit phone number')
  })
})
