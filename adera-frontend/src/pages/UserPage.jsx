import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CustomerShell from '../components/customer/CustomerShell'
import Button from '../components/ui/Button'
import Field from '../components/ui/Field'
import RiskCard from '../components/risk/RiskCard'
import { useAuth } from '../auth/useAuth'
import { checkRisk, simulateTransaction } from '../services/api'

const PHONE_RE = /^0[79]\d{8}$/ // 10 digits starting with 09 or 07

export default function UserPage() {
  const navigate = useNavigate()
  const { signOut } = useAuth()
  const [phone, setPhone] = useState('')
  const [digits, setDigits] = useState('') // amount as plain digits
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [paying, setPaying] = useState(false)

  const amount = Number(digits || 0)
  const shownAmount = digits ? amount.toLocaleString('en-US') : ''
  const sizeClass =
    shownAmount.length > 7 ? ' is-sm' : shownAmount.length > 5 ? ' is-md' : ''
  const canCheck = PHONE_RE.test(phone) && amount > 0 && !loading

  const closeSheet = useCallback(() => setResult(null), [])

  async function handleCheck(e) {
    e.preventDefault()
    if (!canCheck) return
    setLoading(true)
    setError('')
    setNotice('')
    try {
      setResult(await checkRisk(phone, amount))
    } catch (err) {
      const detail = err?.response?.data?.detail
      const status = err?.response?.status
      if (status === 404 && detail === 'Recipient not found') {
        setError('Recipient phone number was not found on the network.')
      } else if (status === 404 && detail === 'Recipient account not found') {
        setError('Recipient has no active payment account.')
      } else if (status === 429) {
        setError('Too many risk checks requested. Please wait a moment and try again.')
      } else {
        setError('Could not check this recipient. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const cancelPayment = () =>
    navigate('/confirmation/cancelled', { state: { phone, amount } })

  // Records the (simulated) payment, then shows the receipt.
  async function handlePay() {
    if (paying) return
    setPaying(true)
    setError('')
    try {
      const payment = await simulateTransaction(phone, amount)
      navigate('/confirmation/sent', {
        state: {
          phone,
          amount,
          reference: payment.id,
          createdAt: payment.created_at,
          level: result?.level,
        },
      })
    } catch {
      setPaying(false)
      setResult(null)
      setError('The payment could not be completed. No money was sent. Please try again.')
    }
  }

  function handleVerify() {
    setResult(null)
    setNotice(
      'Confirm with the person through a number or channel you already trust, then check again.',
    )
  }

  return (
    <CustomerShell back>
      <div className="cu-titlebar">
        <h1 className="cu-title">Send</h1>
        <button type="button" className="cu-signout" onClick={() => signOut()}>
          Sign out
        </button>
      </div>

      <form className="cu-send-form" onSubmit={handleCheck} noValidate>
        <div className="cu-amount">
          <input
            className={`cu-amount-input${sizeClass}`}
            aria-label="Amount in Ethiopian birr"
            inputMode="numeric"
            placeholder="0"
            value={shownAmount}
            onChange={(e) =>
              setDigits(e.target.value.replace(/\D/g, '').replace(/^0+/, '').slice(0, 9))
            }
          />
          <div className="cu-currency">ETB</div>
        </div>

        <Field
          label="Recipient phone"
          mono
          name="recipient"
          inputMode="numeric"
          placeholder="09XXXXXXXX"
          value={phone}
          onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
        />

        {notice && <p className="cu-notice">{notice}</p>}
        {error && <p className="cu-error" role="alert">{error}</p>}

        <div className="cu-bottom">
          <Button type="submit" disabled={!canCheck}>
            {loading ? 'Checking…' : 'Check recipient'}
          </Button>
          <Button
            variant="tertiary"
            style={{ marginTop: 8 }}
            onClick={() => navigate('/report', { state: { phone } })}
          >
            Report suspicious activity
          </Button>
        </div>
      </form>

      {result && (
        <RiskCard
          result={result}
          busy={paying}
          onClose={closeSheet}
          onCancel={cancelPayment}
          onContinue={handlePay}
          onSendAnyway={handlePay}
          onVerify={handleVerify}
        />
      )}
    </CustomerShell>
  )
}