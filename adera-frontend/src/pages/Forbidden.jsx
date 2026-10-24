import { Link } from 'react-router-dom'
import CustomerShell from '../components/customer/CustomerShell'
import { homeFor } from '../auth/access'
import { useAuth } from '../auth/useAuth'

export default function Forbidden() {
  const { user, signOut } = useAuth()
  return (
    <CustomerShell>
      <h1 className="cu-title">No access</h1>
      <p className="cu-notice">
        Your account ({user?.role}) can&apos;t open this page. The analyst area is only for fraud analysts.
      </p>
      <div className="cu-bottom">
        <Link className="ad-btn ad-btn-primary cu-link-btn" to={homeFor(user?.role)}>
          Go to my home page
        </Link>
        <button type="button" className="ad-btn ad-btn-tertiary" style={{ marginTop: 8 }} onClick={() => signOut()}>
          Sign out
        </button>
      </div>
    </CustomerShell>
  )
}
