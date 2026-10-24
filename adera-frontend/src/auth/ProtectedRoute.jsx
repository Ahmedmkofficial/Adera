import { Navigate, Outlet, useLocation } from 'react-router-dom'
import Forbidden from '../pages/Forbidden'
import { useAuth } from './useAuth'

// Wrap routes in this to require a signed-in user, and optionally one role.
export default function ProtectedRoute({ role }) {
  const { user } = useAuth()
  const location = useLocation()

  if (!user) {
    const from = location.pathname + location.search
    const loginPath = role === 'analyst' ? '/analyst/login' : '/login'
    return <Navigate to={loginPath} replace state={{ from }} />
  }
  if (role && user.role !== role) return <Forbidden />
  return <Outlet />
}
