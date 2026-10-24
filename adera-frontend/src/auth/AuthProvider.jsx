import { useCallback, useEffect, useMemo, useState } from 'react'
import { login } from '../services/api'
import { UNAUTHORIZED_EVENT } from '../services/events'
import { AuthContext } from './AuthContext'
import { IDLE_MS } from './constants'
import { clearSession, loadSession, saveSession } from './session'

const ACTIVITY_EVENTS = ['pointerdown', 'keydown', 'touchstart', 'wheel']

export default function AuthProvider({ children }) {
  const [session, setSession] = useState(() => loadSession())
  const [notice, setNotice] = useState(null) // why the last session ended
  const user = session?.user ?? null
  const expiresAt = session?.expiresAt

  // Clearing the session is enough: <ProtectedRoute> sees "nobody is signed in"
  // and sends the visitor to the sign-in page by itself.
  const signOut = useCallback((reason) => {
    clearSession()
    setSession(null)
    setNotice(reason ?? null)
  }, [])

  const signIn = useCallback(async (username, password, expectedRole) => {
    const next = await login(username, password)
    if (expectedRole && next.user.role !== expectedRole) {
      const error = new Error('This account does not have access to this sign-in page.')
      error.code = 'ROLE_MISMATCH'
      throw error
    }
    saveSession(next)
    setSession(next)
    setNotice(null)
    return next.user
  }, [])

  // The server rejected our token.
  useEffect(() => {
    const onUnauthorized = () => signOut('expired')
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
  }, [signOut])

  // The token reached its own expiry time.
  useEffect(() => {
    if (!user || !expiresAt) return undefined
    const timer = setTimeout(() => signOut('expired'), Math.max(0, expiresAt - Date.now()))
    return () => clearTimeout(timer)
  }, [user, expiresAt, signOut])

  // Nothing happened for a while.
  useEffect(() => {
    if (!user) return undefined
    let timer
    const restart = () => {
      clearTimeout(timer)
      timer = setTimeout(() => signOut('idle'), IDLE_MS)
    }
    ACTIVITY_EVENTS.forEach((name) => window.addEventListener(name, restart, { passive: true }))
    restart()
    return () => {
      clearTimeout(timer)
      ACTIVITY_EVENTS.forEach((name) => window.removeEventListener(name, restart))
    }
  }, [user, signOut])

  const value = useMemo(() => ({ user, notice, signIn, signOut }), [user, notice, signIn, signOut])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
