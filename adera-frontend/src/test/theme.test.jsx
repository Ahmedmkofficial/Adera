import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { THEME_KEY } from '../theme/ThemeProvider'
import { renderApp } from './helpers'

describe('appearance preferences', () => {
  it('loads the saved theme and persists a toggle across a new app mount', async () => {
    localStorage.setItem(THEME_KEY, 'light')
    const user = userEvent.setup()
    const firstRender = renderApp('/login')

    expect(document.documentElement.dataset.theme).toBe('light')
    await user.click(screen.getByRole('button', { name: 'Switch to dark theme' }))
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')

    firstRender.unmount()
    renderApp('/admin')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })
})
