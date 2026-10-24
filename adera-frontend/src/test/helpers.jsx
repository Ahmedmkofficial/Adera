import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import AuthProvider from '../auth/AuthProvider'
import ThemeProvider from '../theme/ThemeProvider'
import { INTRO_SESSION_KEY, SESSION_KEY } from '../auth/constants'
import LocationProbe from './LocationProbe'

export const CUSTOMER = { username: '0911000001', name: 'Hana Abate', role: 'customer' }
export const ANALYST = { username: 'admin', name: 'Admin', role: 'analyst' }

// Pretend someone already signed in, without going through the form.
export function signInAs(user, extra = {}) {
  sessionStorage.setItem(
    SESSION_KEY,
    JSON.stringify({ token: 'test-token', user, expiresAt: Date.now() + 3600_000, ...extra }),
  )
}

export function renderApp(path = '/', { showIntro = false, trackLocation = false } = {}) {
  if (showIntro) sessionStorage.removeItem(INTRO_SESSION_KEY)
  else sessionStorage.setItem(INTRO_SESSION_KEY, 'true')
  return render(
    <MemoryRouter initialEntries={[path]}>
      <>
        {trackLocation && <LocationProbe />}
        <ThemeProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </ThemeProvider>
      </>
    </MemoryRouter>,
  )
}
