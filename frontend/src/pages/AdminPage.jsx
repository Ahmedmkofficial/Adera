import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api'

function displayDate(value) {
	if (!value) return '—'
	const date = new Date(value)
	return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function DetailDisclosure({ summary, load, children: renderDetails }) {
	const [details, setDetails] = useState(null)
	const [error, setError] = useState('')
	const [loading, setLoading] = useState(false)

	async function openDetails(event) {
		if (!event.currentTarget.open || details || loading) return
		setLoading(true)
		setError('')
		try {
			setDetails(await load())
		} catch (requestError) {
			setError(requestError.message)
		} finally {
			setLoading(false)
		}
	}

	return <details className="record-details" onToggle={openDetails}>
		<summary>{summary}</summary>
		{loading && <p className="detail-loading">Loading record details…</p>}
		{error && <p className="detail-error" role="alert">{error}</p>}
		{details && renderDetails(details)}
	</details>
}

function AlertDetail({ data }) {
	const alert = data.alert || {}
	const assessment = data.risk_assessment
	return <div className="detail-content">
		<div className="detail-facts">
			<div><span>Alert message</span><strong>{alert.message || 'No message supplied'}</strong></div>
			<div><span>Recipient</span><strong>{alert.recipient_phone || '—'}</strong></div>
			<div><span>Received</span><strong>{displayDate(alert.created_at)}</strong></div>
		</div>
		{assessment ? <div className="assessment-detail"><strong>Recorded assessment</strong><span>{assessment.level} · {assessment.score}/100</span><span>Recommendation: {assessment.recommendation?.replaceAll('_', ' ') || '—'}</span><small>Rule explanations are not included in the existing alert-detail response.</small></div> : <p className="detail-empty">No linked risk assessment is available for this alert.</p>}
	</div>
}

function CaseDetail({ data }) {
	const item = data.case || {}
	return <div className="detail-content">
		<div className="detail-facts">
			<div><span>Investigation description</span><strong>{item.description || 'No description supplied'}</strong></div>
			<div><span>Scam type</span><strong>{item.scam_type || '—'}</strong></div>
			<div><span>Analyst decision</span><strong>{item.decision || 'Not recorded'}</strong></div>
			{item.decision_notes && <div><span>Decision notes</span><strong>{item.decision_notes}</strong></div>}
		</div>
		{data.risk_assessment && <div className="assessment-detail"><strong>Latest recipient assessment</strong><span>{data.risk_assessment.level} · {data.risk_assessment.score}/100</span><span>Recommendation: {data.risk_assessment.recommendation?.replaceAll('_', ' ') || '—'}</span><small>Rule explanations are not included in the existing case-detail response.</small></div>}
		{data.fraud_reports?.length > 0 && <div className="detail-list"><h4>Reports on this recipient <span>{data.fraud_reports.length}</span></h4>{data.fraud_reports.map((report) => <article key={report.id}><div><strong>{report.scam_type}</strong><small>Report #{report.id} · {displayDate(report.created_at)}</small></div><p>{report.description}</p></article>)}</div>}
		{data.relevant_transactions?.length > 0 && <div className="detail-list"><h4>Recent simulated transfers <span>{data.relevant_transactions.length}</span></h4>{data.relevant_transactions.map((transaction, index) => <article key={`${transaction.created_at}-${index}`}><div><strong>ETB {Number(transaction.amount).toLocaleString()}</strong><small>{displayDate(transaction.created_at)}</small></div><span className="status-pill">{transaction.status}</span></article>)}</div>}
	</div>
}

export default function AdminPage() {
	const [alerts, setAlerts] = useState([])
	const [cases, setCases] = useState([])
	const [error, setError] = useState('')
	const [loading, setLoading] = useState(true)

	const refresh = useCallback(async () => {
		setLoading(true)
		setError('')
		try {
			const [alertData, caseData] = await Promise.all([api.getAlerts(), api.getCases()])
			setAlerts(alertData)
			setCases(caseData)
		} catch (requestError) {
			setError(requestError.message)
		} finally {
			setLoading(false)
		}
	}, [])

	useEffect(() => {
		let active = true
		Promise.all([api.getAlerts(), api.getCases()])
			.then(([alertData, caseData]) => {
				if (active) {
					setAlerts(alertData)
					setCases(caseData)
				}
			})
			.catch((requestError) => {
				if (active) setError(requestError.message)
			})
			.finally(() => {
				if (active) setLoading(false)
			})
		return () => { active = false }
	}, [])

	return <div className="analyst-page">
		<div className="page-heading"><div><p className="eyebrow">ANALYST WORKSPACE</p><h1>Investigation desk</h1><p className="muted">Review risk alerts and follow active scam cases.</p></div><div className="dashboard-actions"><span className="demo-label"><span />LOCAL DEMO <b>/</b> SYNTHETIC DATA</span><button className="button button-outline" onClick={refresh} disabled={loading}>{loading ? 'Refreshing…' : '↻ Refresh'}</button></div></div>
		{error && <div className="notice notice-error" role="alert"><strong>Dashboard data unavailable</strong><span>{error}. Sign in with an ANALYST or ADMIN account and confirm the backend has records to display.</span></div>}
		<div className="metric-grid"><article className="metric-card metric-alert"><span>OPEN ALERTS</span><strong>{loading ? '—' : alerts.filter((alert) => alert.status === 'OPEN').length}</strong><small>Require analyst attention</small></article><article className="metric-card"><span>ALERTS LOADED</span><strong>{loading ? '—' : alerts.length}</strong><small>Risk-triggered notifications</small></article><article className="metric-card"><span>SCAM CASES</span><strong>{loading ? '—' : cases.length}</strong><small>Investigation records</small></article></div>
		<section className="panel table-panel"><div className="panel-heading"><div><span className="section-kicker">PRIORITIZE</span><h2>Risk alerts</h2></div><span className="count-badge">{alerts.length}</span></div>
			{loading ? <p className="empty-state">Loading alerts…</p> : alerts.length === 0 ? <p className="empty-state">No alerts to review. High-risk checks create alerts automatically.</p> : <div className="record-list">
				<div className="record-grid record-header alert-grid"><span>Recipient / alert</span><span>Severity</span><span>Score</span><span>Status</span><span>Received</span></div>
				{alerts.map((alert) => <article className="record-row" key={alert.id}>
					<div className="record-grid alert-grid">
						<div className="record-primary"><strong>{alert.recipient_phone}</strong><small>Alert #{alert.id}</small></div>
						<div><span className={`status-pill risk-${(alert.risk_level || alert.severity || 'low').toLowerCase()}`}>{alert.risk_level || alert.severity || '—'}</span></div>
						<div className="score-cell">{alert.risk_score != null ? <><strong>{alert.risk_score}</strong><small>/ 100</small></> : <span className="muted">—</span>}</div>
						<div><span className={`status-pill status-${String(alert.status).toLowerCase()}`}>{alert.status}</span></div>
						<time className="record-date" dateTime={alert.created_at}>{displayDate(alert.created_at)}</time>
					</div>
					<DetailDisclosure summary="View alert details" load={() => api.getAlertDetail(alert.id)}>{(data) => <AlertDetail data={data} />}</DetailDisclosure>
				</article>)}
			</div>}
		</section>
		<section className="panel table-panel"><div className="panel-heading"><div><span className="section-kicker">FOLLOW UP</span><h2>Scam cases</h2></div><span className="count-badge">{cases.length}</span></div>
			{loading ? <p className="empty-state">Loading cases…</p> : cases.length === 0 ? <p className="empty-state">No cases yet. An analyst can open a case from an alert in the API workflow.</p> : <div className="record-list">
				<div className="record-grid record-header case-grid"><span>Case / ID</span><span>Recipient</span><span>Type</span><span>Status</span><span>Opened</span></div>
				{cases.map((item) => <article className="record-row" key={item.id}>
					<div className="record-grid case-grid">
						<div className="record-primary"><strong>{item.title}</strong><small>Case #{item.id}</small></div>
						<div className="record-secondary">{item.recipient_phone}</div>
						<div className="record-secondary">{item.scam_type || '—'}</div>
						<div><span className={`status-pill status-${String(item.status).toLowerCase()}`}>{item.status}</span></div>
						<time className="record-date" dateTime={item.created_at}>{displayDate(item.created_at)}</time>
					</div>
					<DetailDisclosure summary="View investigation details" load={() => api.getCaseDetail(item.id)}>{(data) => <CaseDetail data={data} />}</DetailDisclosure>
				</article>)}
			</div>}
		</section>
	</div>
}
