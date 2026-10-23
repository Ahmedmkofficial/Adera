const API_BASE = '/api'
const TOKEN_KEY = 'adera_access_token'

async function request(path, { method = 'GET', body, auth = true } = {}) {
	const headers = { Accept: 'application/json' }
	if (body !== undefined) headers['Content-Type'] = 'application/json'
	const token = localStorage.getItem(TOKEN_KEY)
	if (auth && token) headers.Authorization = `Bearer ${token}`

	let response
	try {
		response = await fetch(`${API_BASE}${path}`, {
			method,
			headers,
			body: body === undefined ? undefined : JSON.stringify(body),
		})
	} catch {
		throw new Error('Cannot reach Adera API. Check that the backend is running.')
	}

	const data = response.status === 204 ? null : await response.json().catch(() => null)
	if (!response.ok) {
		const detail = data?.detail
		const message = Array.isArray(detail)
			? detail.map((item) => item.msg).join('; ')
			: detail || `Request failed (${response.status})`
		if (response.status === 401 && auth) {
			localStorage.removeItem(TOKEN_KEY)
			window.dispatchEvent(new Event('adera:unauthorized'))
		}
		throw new Error(message)
	}
	return data
}

export const api = {
	getToken: () => localStorage.getItem(TOKEN_KEY),
	setToken: (token) => localStorage.setItem(TOKEN_KEY, token),
	logout: () => localStorage.removeItem(TOKEN_KEY),
	register: (payload) => request('/auth/register', { method: 'POST', body: payload, auth: false }),
	login: (payload) => request('/auth/login', { method: 'POST', body: payload, auth: false }),
	me: () => request('/auth/me'),
	checkRisk: (payload) => request('/risk/check', { method: 'POST', body: payload }),
	submitReport: (payload) => request('/reports', { method: 'POST', body: payload }),
	getAlerts: () => request('/alerts'),
	getAlertDetail: (id) => request(`/alerts/${id}`),
	getCases: () => request('/cases'),
	getCaseDetail: (id) => request(`/cases/${id}`),
}
