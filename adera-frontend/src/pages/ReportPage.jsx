import { useId, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import CustomerShell from '../components/customer/CustomerShell'
import Button from '../components/ui/Button'
import Field from '../components/ui/Field'
import { submitReport } from '../services/api'

const PHONE_RE = /^0[79]\d{8}$/ // 10 digits starting with 09 or 07
const SCAM_TYPES = ['Impersonation', 'Fake investment', 'Prize or lottery', 'Other']
const MAX_DESCRIPTION = 500

export default function ReportPage() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const descriptionId = useId()

  const [phone, setPhone] = useState(state?.phone ?? '')
  const [type, setType] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!PHONE_RE.test(phone)) {
      setError('Enter a 10-digit phone number starting with 09 or 07.')
      return
    }
    if (!type) {
      setError('Choose the type of activity.')
      return
    }
    if (description.trim().length < 10) {
      setError('Describe what happened in at least 10 characters.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await submitReport({
        recipient_phone: phone,
        scam_type: type,
        description: description.trim(),
      })
      navigate('/confirmation/reported')
    } catch {
      setError('Could not submit your report. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <CustomerShell back>
      <h1 className="cu-title">Report</h1>

      <form className="cu-report-form" onSubmit={handleSubmit} noValidate>
        <div className="cu-fields">
          <Field
            label="Recipient phone"
            mono
            name="recipient"
            inputMode="numeric"
            placeholder="09XXXXXXXX"
            value={phone}
            onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
          />

          <fieldset className="cu-types">
            <legend className="ad-field-label">Type of activity</legend>
            {SCAM_TYPES.map((t) => (
              <label key={t} className={`cu-type${type === t ? ' is-on' : ''}`}>
                <input
                  type="radio"
                  name="scam_type"
                  value={t}
                  checked={type === t}
                  onChange={() => setType(t)}
                />
                <span className="cu-type-node" aria-hidden="true" />
                <span>{t}</span>
              </label>
            ))}
          </fieldset>

          <div>
            <label className="ad-field-label" htmlFor={descriptionId}>
              What happened?
            </label>
            <textarea
              id={descriptionId}
              className="cu-textarea"
              rows={4}
              maxLength={MAX_DESCRIPTION}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <div className="cu-count">
              {description.length}/{MAX_DESCRIPTION}
            </div>
          </div>
        </div>

        {error && <p className="cu-error" role="alert">{error}</p>}

        <div className="cu-bottom">
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit report'}
          </Button>
        </div>
      </form>
    </CustomerShell>
  )
}