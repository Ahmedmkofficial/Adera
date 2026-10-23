import { useNavigate } from 'react-router-dom'
import LogoMark from '../LogoMark'
import SkipLink from '../SkipLink'
import './customer.css'

// back: show a back arrow (the logo moves to the right).
// mark: show the logo in the top bar (turned off on sign-in pages, which show it large).
export default function CustomerShell({ back = false, mark = true, children }) {
  const navigate = useNavigate()
  return (
    <div className="cu-shell">
      <SkipLink />
      <header className="cu-topbar">
        {back ? (
          <button type="button" className="cu-back" aria-label="Go back" onClick={() => navigate(-1)}>
            ‹
          </button>
        ) : mark ? (
          <LogoMark size={30} title="Adera" />
        ) : (
          <span />
        )}
        {back && <LogoMark size={26} title="Adera" />}
      </header>
      <main id="main" tabIndex={-1} className="cu-content">{children}</main>
    </div>
  )
}
