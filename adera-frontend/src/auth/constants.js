export const ROLES = ['customer', 'analyst']
export const IDLE_MS = 15 * 60 * 1000 // sign out after 15 minutes without activity
export const SESSION_KEY = 'adera.session'

export const SIGN_OUT_NOTICES = {
  idle: 'You were signed out after 15 minutes of inactivity. Sign in again to continue.',
  expired: 'Your session has ended. Sign in again to continue.',
  registered: 'Account created. Sign in to continue.',
}
