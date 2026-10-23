import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ANALYST, renderApp, signInAs } from './helpers'

describe('relationship graph', () => {
  it('draws the network and lets an analyst inspect each node', async () => {
    const user = userEvent.setup()
    signInAs(ANALYST)
    renderApp('/admin/entity/0912345678/graph')
    expect(await screen.findByRole('heading', { name: 'Connected entities' })).toBeInTheDocument()
    expect(screen.getByText(/3 accounts · showing 3 of 7 reports/)).toBeInTheDocument()
    expect(screen.getByText('Recipient account')).toBeInTheDocument()
    expect(document.querySelectorAll('.react-flow__node')).toHaveLength(6)

    await user.click(screen.getByRole('button', { name: '0927804412' }))
    expect(screen.getByText('Related account')).toBeInTheDocument()
    expect(screen.getByText('SHARED_PHONE', { selector: 'dd' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'REPORT-42' }))
    expect(screen.getByText('Fraud report', { selector: 'dd' })).toBeInTheDocument()
  })

  it('says so when there is nothing to draw', async () => {
    signInAs(ANALYST)
    renderApp('/admin/entity/0900000000/graph')
    expect(await screen.findByRole('heading', { name: 'No record found' })).toBeInTheDocument()
  })
})
