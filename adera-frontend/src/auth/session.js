import { ROLES, SESSION_KEY } from './constants'

// The session is kept in sessionStorage: it survives a refresh but disappears
// when the tab closes. Anything in browser storage can be read by a script that
// runs on the page (XSS), so the app never renders user text as HTML.
// Production would use an httpOnly cookie instead. See docs/SECURITY.md.

function isValidSession(s) {
  return Boolean(
    s &&
      typeof s.token === 'string' &&
      s.token.length > 0 &&
      s.user &&
      typeof s.user.username === 'string' &&
      typeof s.user.name === 'string' &&
      ROLES.includes(s.user.role) &&
      (s.expiresAt === undefined || (typeof s.expiresAt === 'number' && s.expiresAt > Date.now())),
  )
}

export function loadSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (isValidSession(parsed)) return parsed
    sessionStorage.removeItem(SESSION_KEY) // damaged or tampered: throw it away
  } catch {
    // storage blocked or unreadable: behave as signed out
  }
  return null
}

export function saveSession(session) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(session))
  } catch {
    // storage blocked: the session just won't survive a refresh
  }
}

export function clearSession() {
  try {
    sessionStorage.removeItem(SESSION_KEY)
  } catch {
    // nothing to clear
  }
}

export const getToken = () => loadSession()?.token ?? null

// Reads the claims inside a JWT. This is for display only (name, role, expiry);
// the server is the one that decides what the token allows.
export function decodeJwtPayload(token) {
  try {
    const part = token.split('.')[1]
    const base64 = part.replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4)
    return JSON.parse(atob(padded))
  } catch {
    return null
  }
}
