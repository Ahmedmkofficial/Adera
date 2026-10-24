import { useId } from 'react'
import './ui.css'

export default function Field({ label, mono = false, ...props }) {
  const id = useId()
  return (
    <div className="ad-field">
      <label className="ad-field-label" htmlFor={id}>{label}</label>
      <input id={id} className={`ad-field-input${mono ? ' mono' : ''}`} {...props} />
    </div>
  )
}