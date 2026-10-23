import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import AuthProvider from '../auth/AuthProvider'
import { SESSION_KEY } from '../auth/constants'

export const CUSTOMER = { username: '0911000001', name: 'Hana Abate', role: 'customer' }
export const ANALYST = { username: 'admin', name: 'Admin', role: 'analyst' }

// Pretend someone already signed in, without going through the form.
export function signInAs(user, extra = {}) {
  sessionStorage.setItem(
    SESSION_KEY,
    JSON.stringify({ token: 'test-token', user, expiresAt: Date.now() + 3600_000, ...extra }),
  )
}

export function renderApp(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  )
}
