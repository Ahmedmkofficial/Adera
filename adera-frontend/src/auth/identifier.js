// What a person types into the first sign-in box: a phone number (customers)
// or a username (staff). These checks are for convenience; the server checks again.
export const PHONE_RE = /^0[79]\d{8}$/ // 10 digits starting with 09 or 07
export const USERNAME_RE = /^[a-z][a-z0-9._-]{2,31}$/i

// Returns an error message, or '' when the value looks fine.
export function checkIdentifier(raw) {
  const value = raw.trim()
  if (!value) return 'Enter your phone number or username.'
  if (/^\d+$/.test(value)) {
    return PHONE_RE.test(value) ? '' : 'Enter a 10-digit phone number starting with 09 or 07.'
  }
  return USERNAME_RE.test(value) ? '' : 'Enter your phone number or username.'
}

// Usernames are not case-sensitive.
export const normalizeIdentifier = (raw) => raw.trim().toLowerCase()
