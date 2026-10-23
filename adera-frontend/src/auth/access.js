// Where each role starts, and which addresses each role may open.
// This only decides what the screen shows. The backend must check again.
export const homeFor = (role) => (role === 'analyst' ? '/admin' : '/')

export const canVisit = (role, path) =>
  typeof path === 'string' && (path.startsWith('/admin') ? role === 'analyst' : true)

// After signing in, go back to the page the visitor first asked for, but only if
// it belongs to their own area. Otherwise go to their home page. (An analyst who
// opened the plain address "/" first should still land in the analyst area.)
export function destinationFor(role, from) {
  if (typeof from !== 'string' || !canVisit(role, from)) return homeFor(role)
  if (role === 'analyst' && !from.startsWith('/admin')) return homeFor(role)
  return from
}
