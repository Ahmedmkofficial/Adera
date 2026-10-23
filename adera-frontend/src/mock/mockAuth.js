// Accounts for the built-in demo data. Passwords sit in plain text here ONLY because
// this is fake data that disappears from a real-backend build. The real backend must
// store password hashes, and must not ship a default admin/admin account.
const USERS = [
  { username: 'admin', name: 'Admin', role: 'analyst', password: 'admin' },
  { username: '0911000001', name: 'Hana Abate', role: 'customer', password: 'demo-customer-1' },
]

const SESSION_MS = 60 * 60 * 1000 // tokens last one hour
const delay = (value, ms = 350) => new Promise((resolve) => setTimeout(() => resolve(value), ms))
const fail = (status, message) => Promise.reject(Object.assign(new Error(message), { status }))

const b64url = (object) =>
  btoa(JSON.stringify(object)).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')

// JWT-shaped so the app's token handling can be exercised. It is NOT signed.
function makeToken(user) {
  const claims = {
    sub: user.username,
    name: user.name,
    role: user.role,
    exp: Math.floor((Date.now() + SESSION_MS) / 1000),
  }
  return `${b64url({ alg: 'none', typ: 'JWT' })}.${b64url(claims)}.mock`
}

export function mockLogin(username, password) {
  const user = USERS.find((u) => u.username === String(username).toLowerCase())
  if (!user || user.password !== password) return fail(401, 'Invalid sign-in details')
  return delay({
    access_token: makeToken(user),
    token_type: 'bearer',
    user: { username: user.username, name: user.name, role: user.role },
  })
}

export function mockRegister({ phone, name, password }) {
  if (USERS.some((u) => u.username === phone)) return fail(409, 'Phone number already registered')
  USERS.push({ username: phone, name, password, role: 'customer' }) // new accounts are always customers
  return delay({ phone, name, role: 'customer' })
}
