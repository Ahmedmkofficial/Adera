import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { INTRO_SESSION_KEY } from '../auth/constants'
import { ANALYST, renderApp, signInAs } from './helpers'

describe('login logo animation', () => {
  it('draws the original fingerprint ridges inside the shield before revealing the form', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    renderApp('/login', { showIntro: true, trackLocation: true })

    const mark = document.querySelector('.cu-wordmark-mark')
    expect(mark).toHaveAttribute('viewBox', '0 0 48 48')
    const shield = mark.querySelector('path[stroke="currentColor"]')
    expect(shield).toHaveAttribute(
      'd',
      'M24 3.2 41 9.4v10.8c0 10.5-6.4 19.2-17 24.6C13.4 39.4 7 30.7 7 20.2V9.4L24 3.2Z',
    )
    expect(shield).toHaveAttribute('stroke-width', '2.2')
    const ridges = Array.from(mark.querySelectorAll('g path'))
    expect(ridges.map((ridge) => ridge.getAttribute('d'))).toEqual([
      'M14.5 21.4a9.5 9.5 0 0 1 19 0',
      'M17.5 21.4a6.5 6.5 0 0 1 13 0',
      'M20.5 21.4a3.5 3.5 0 0 1 7 0c0 7.1-1.2 11.4-3.5 14.1',
      'M14.7 25.2c.5 4.3 1.9 7.9 4.3 10.5',
      'M33.3 25.2c-.4 4.2-1.5 7.5-3.4 10.2',
      'M24 21.4v8.8',
    ])
    expect(ridges).toHaveLength(6)
    expect(mark.querySelector('g')).toHaveAttribute('stroke', 'var(--logo-line, currentColor)')
    expect(mark.querySelector('.ad-login-logo-ridge-center')).toHaveAttribute('d', 'M24 21.4v8.8')
    expect(document.querySelector('.ad-intro')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Skip intro' })).not.toBeInTheDocument()
    expect(document.querySelector('.cu-login-form')).toHaveAttribute('inert')
    expect(screen.getByTestId('current-path')).toHaveTextContent('/login')

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1300)
    })
    expect(screen.getByTestId('current-path')).toHaveTextContent('/login')
    expect(document.querySelector('.cu-login-form')).toHaveAttribute('inert')

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1300)
    })

    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
    expect(document.querySelector('.cu-login-form')).not.toHaveAttribute('inert')
    expect(mark.querySelector('.ad-login-logo-ridge')).not.toBeInTheDocument()
    expect(screen.getByTestId('current-path')).toHaveTextContent('/login')
    expect(sessionStorage.getItem(INTRO_SESSION_KEY)).toBe('true')
  })

  it('keeps the login form and logo on the same root URL', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    renderApp('/', { showIntro: true, trackLocation: true })
    expect(document.querySelector('.ad-intro')).not.toBeInTheDocument()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600)
    })

    expect(screen.getByLabelText('Phone number')).toBeInTheDocument()
    expect(screen.getByTestId('current-path')).toHaveTextContent('/')
  })

  it('preserves the analyst login page and animates its existing logo in place', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    renderApp('/analyst/login', { showIntro: true, trackLocation: true })
    expect(document.querySelector('.ad-intro')).not.toBeInTheDocument()
    expect(document.querySelector('.cu-wordmark-mark')).toHaveAttribute('viewBox', '0 0 48 48')

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600)
    })

    expect(screen.getByLabelText('Staff username or phone number')).toBeInTheDocument()
    expect(screen.getByTestId('current-path')).toHaveTextContent('/analyst/login')
  })

  it('does not replay when switching between the login pages', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    renderApp('/login', { showIntro: true })
    expect(document.querySelector('.ad-intro')).not.toBeInTheDocument()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2600)
    })
    await user.click(screen.getByRole('link', { name: 'Analyst or admin? Sign in here' }))

    expect(await screen.findByLabelText('Staff username or phone number')).toBeInTheDocument()
    expect(document.querySelector('.ad-intro')).not.toBeInTheDocument()
    expect(document.querySelector('.ad-login-logo-ridge')).not.toBeInTheDocument()
  })

  it('shows the login immediately when reduced motion is requested', async () => {
    const descriptor = Object.getOwnPropertyDescriptor(window, 'matchMedia')
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      value: () => ({ matches: true }),
    })
    try {
      renderApp('/login', { showIntro: true })
      expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
      expect(document.querySelector('.ad-intro')).not.toBeInTheDocument()
      expect(document.querySelector('.ad-login-logo-ridge')).not.toBeInTheDocument()
    } finally {
      if (descriptor) Object.defineProperty(window, 'matchMedia', descriptor)
      else delete window.matchMedia
    }
  })

  it('does not show the intro to an authenticated user after refresh', async () => {
    signInAs(ANALYST)
    renderApp('/admin', { showIntro: true })

    expect(await screen.findByRole('heading', { name: 'Overview' })).toBeInTheDocument()
    expect(document.querySelector('.ad-intro')).not.toBeInTheDocument()
    expect(sessionStorage.getItem(INTRO_SESSION_KEY)).toBeNull()
  })
})
