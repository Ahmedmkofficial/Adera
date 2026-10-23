import { useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { api } from '../services/api'

function ResultCard({ result }) {
	return (
		<section className={`result-card risk-${result.level.toLowerCase()}`} aria-live="polite">
			<div className="result-topline"><span className="eyebrow">RECIPIENT RISK RESULT</span><span className="risk-pill">{result.level}</span></div>
			<div className="score-row"><strong>{result.score}</strong><span> / 100<br /><small>risk score</small></span></div>
			<div className="score-track"><span style={{ width: `${result.score}%` }} /></div>
			<div className="recommendation"><span>Recommended action</span><strong>{result.recommendation.replaceAll('_', ' ')}</strong></div>
			<div className="reason-list"><h3>What informed this result</h3>
				{result.reasons?.length ? <ul>{result.reasons.map((reason, index) => <li key={`${reason}-${index}`}>{reason}</li>)}</ul> : <p className="muted">No additional risk signals were returned.</p>}
			</div>
			<p className="small-note">This check is decision support and does not guarantee a payment outcome.</p>
		</section>
	)
}

function RiskCheck() {
	const [form, setForm] = useState({ recipient_phone: '', amount: '' })
	const [result, setResult] = useState(null)
	const [error, setError] = useState('')
	const [busy, setBusy] = useState(false)

	async function submit(event) {
		event.preventDefault()
		setError('')
		setResult(null)
		setBusy(true)
		try {
			setResult(await api.checkRisk({ recipient_phone: form.recipient_phone.trim(), amount: Number(form.amount) }))
		} catch (requestError) {
			setError(requestError.message)
		} finally {
			setBusy(false)
		}
	}

	return <>
		<div className="page-heading"><div><p className="eyebrow">BEFORE YOU SEND</p><h1>Check a recipient</h1><p className="muted">Review available recipient signals before a mobile-money transfer.</p></div><span className="heading-icon">◎</span></div>
		<div className="user-grid">
			<section className="panel form-panel"><div className="panel-heading"><div><span className="step-number">01</span><h2>Payment details</h2></div><span className="secure-label">● Secure check</span></div>
				<form className="form-stack" onSubmit={submit}>
					<label>Recipient mobile number<input required minLength="7" maxLength="20" inputMode="tel" placeholder="e.g. 0912345678" value={form.recipient_phone} onChange={(event) => setForm({ ...form, recipient_phone: event.target.value })} /></label>
					<label>Transfer amount <span className="field-hint">ETB</span><input required type="number" min="0.01" step="0.01" inputMode="decimal" placeholder="0.00" value={form.amount} onChange={(event) => setForm({ ...form, amount: event.target.value })} /></label>
					{error && <div className="notice notice-error" role="alert"><strong>Check could not be completed</strong><span>{error}{error.toLowerCase().includes('recipient') ? ' The recipient must already have an Adera account and payment account.' : ''}</span></div>}
					<button className="button button-primary button-wide" disabled={busy}>{busy ? 'Checking recipient…' : 'Check risk'}</button>
				</form>
				<div className="privacy-note"><span>◈</span><p>Your check uses existing Adera report and account signals. Adera does not move money.</p></div>
			</section>
			<aside className="side-panel"><div className="side-icon">✳</div><h3>Pause. Verify. Then transfer.</h3><p>Scammers often create urgency. Confirm the recipient through a trusted channel before sending money.</p><Link className="inline-link" to="/user/report">Report suspicious activity <span>→</span></Link></aside>
		</div>
		{result && <ResultCard result={result} />}
		<section className="panel report-cta"><div><p className="eyebrow">HELP PROTECT THE COMMUNITY</p><h2>Experienced something suspicious?</h2><p className="muted">Share a report so it can be reviewed and help inform future checks.</p></div><Link className="button button-outline" to="/user/report">Submit a report <span>→</span></Link></section>
	</>
}

function ReportForm() {
	const [form, setForm] = useState({ recipient_phone: '', scam_type: '', description: '' })
	const [message, setMessage] = useState('')
	const [error, setError] = useState('')
	const [busy, setBusy] = useState(false)

	async function submit(event) {
		event.preventDefault()
		setBusy(true)
		setError('')
		setMessage('')
		try {
			const report = await api.submitReport({ ...form, recipient_phone: form.recipient_phone.trim(), scam_type: form.scam_type.trim(), description: form.description.trim() })
			setMessage(`Report #${report.id} submitted. Its current status is ${report.status}.`)
			setForm({ recipient_phone: '', scam_type: '', description: '' })
		} catch (requestError) {
			setError(requestError.message)
		} finally {
			setBusy(false)
		}
	}

	return <>
		<div className="page-heading"><div><p className="eyebrow">COMMUNITY REPORTING</p><h1>Report a scam</h1><p className="muted">Provide clear details. Reports are submitted as pending review.</p></div><Link className="back-link" to="/user">← Back to risk check</Link></div>
		<section className="panel report-form-panel"><div className="panel-heading"><div><span className="step-number">02</span><h2>What happened?</h2></div><span className="secure-label">Private submission</span></div>
			<form className="form-stack" onSubmit={submit}>
				<label>Recipient mobile number<input required minLength="7" maxLength="20" inputMode="tel" placeholder="Phone number involved" value={form.recipient_phone} onChange={(event) => setForm({ ...form, recipient_phone: event.target.value })} /></label>
				<label>Scam type<input required minLength="2" maxLength="50" placeholder="e.g. IMPERSONATION, FAKE_SELLER" value={form.scam_type} onChange={(event) => setForm({ ...form, scam_type: event.target.value })} /><span className="field-help">Use a short category name. The API accepts a text value.</span></label>
				<label>Description<textarea required minLength="10" maxLength="2000" rows="5" placeholder="Include what was requested, when it happened, and any steps you took to verify…" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /><span className="field-help">{form.description.length}/2000 characters. Do not include your PIN or OTP.</span></label>
				{message && <div className="notice notice-success" role="status">{message}</div>}
				{error && <div className="notice notice-error" role="alert">{error}</div>}
				<div className="form-actions"><p className="small-note">Your account is attached as the reporter.</p><button className="button button-primary" disabled={busy}>{busy ? 'Submitting…' : 'Submit report'}</button></div>
			</form>
		</section>
	</>
}

export default function UserPage({ initialView = 'risk' }) {
	const { user } = useOutletContext()
	return <div className="user-page" data-user={user?.id}>{initialView === 'report' ? <ReportForm /> : <RiskCheck />}</div>
}
