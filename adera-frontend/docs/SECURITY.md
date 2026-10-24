# Security notes

This is a prototype with synthetic data, but it is built the way a real app should be. These notes are written for the cybersecurity course.

## The most important rule

**Anything the browser checks, an attacker can skip.** Everything the frontend does about security (hiding pages, checking forms, ending sessions) is for the user's convenience. **The backend must enforce every rule again.**

| What the frontend does | What the backend must also do |
|---|---|
| Hides `/admin` from customers (`ProtectedRoute`) | Reject customer tokens on every analyst endpoint with `403` |
| Checks phone format, password length, report length | Validate and limit every field; return `422` |
| Shows one generic message for a wrong sign-in | Return the same `401` for wrong phone and wrong password; rate-limit attempts |
| Ends the screen session after 15 idle minutes | Expire tokens on the server (short lifetime) |
| Asks "are you sure?" before closing a case | Reject decisions on closed cases |
| Never sends who made a decision | Take the decision-maker from the token, never from the request body |

## What the frontend does

**Authentication and sessions**
- Sign-in state lives in `src/auth/`. Roles are `customer` and `analyst`; new accounts are always customers.
- The session (token and user) is stored in `sessionStorage`: it survives a refresh but is gone when the tab closes. A stored session is validated on load (shape, known role, not expired); damaged or hand-edited data is thrown away.
- The session ends after 15 minutes without activity, when the token expires, and when the server answers `401` to a normal request. The reason is shown on the sign-in page.
- Sign-in errors never say which of phone or password was wrong. A `401` from the sign-in form itself is not treated as "session ended".

**Cross-site scripting (XSS)**
- Customer-written text (report descriptions) is shown to analysts. React displays it as plain text. The code contains **no** `dangerouslySetInnerHTML`, `innerHTML`, `eval` or `new Function` (checked: 0 matches).
- URL parts (phone numbers, ids) are encoded with `encodeURIComponent` before being placed in an API path.
- No outside requests: fonts are self-hosted, so there is no third-party script or font host.

**Other**
- No secrets in the repository. Settings live in `.env`, which is git-ignored; `.env.example` shows the names.
- Payments are only ever *simulated*. Sending twice is blocked while a payment is in progress.
- `npm audit`: 0 known vulnerabilities at the time of writing.

## Known trade-offs (say these in the report)

1. **Token in `sessionStorage`.** Any script that runs on the page can read it. Production should use an `httpOnly`, `Secure`, `SameSite` cookie, which scripts cannot read, plus CSRF protection.
2. **Default credentials (`admin` / `admin`) exist in the built-in data** (`src/mock/mockAuth.js`) and are shown on the sign-in page in demo mode. They are left out of the build when `VITE_USE_MOCK=false` (checked by building both ways). The real backend must store password **hashes** (bcrypt or argon2), never passwords.
3. **The JWT is decoded in the browser only to show a name and an expiry.** It is not verified there (it cannot be). The server decides what a token allows.
4. **No client-side rate limiting.** It would not stop an attacker, who can call the API directly. Limit sign-in attempts on the server.

## Default credentials

The built-in data includes an `admin` account whose password is `admin`. Default and guessable credentials are one of the most common ways real systems are broken into (OWASP: Identification and Authentication Failures), and `admin`/`admin` is the first pair any attacker tries. Here it is acceptable because:

- it only works against fake data, with no backend;
- it is removed from the build when `VITE_USE_MOCK=false`, which is how the real system must run;
- the sign-in page does not display it.

**The real backend must not ship a default admin account.** Create analyst accounts with a unique strong password each, require a password change on first sign-in, and lock or slow down repeated failed attempts.

## Backend checklist (to give the backend team)

- HTTPS only; restrictive CORS (only the frontend's origin).
- Role checks on every route; analyst-only data (`/recipients/*`, `/alerts*`, `/cases*`, `/dashboard/*`) never reachable with a customer token.
- Short token lifetime; reject expired tokens.
- Validate input length and type; escape/limit stored text.
- Log who did what (decisions are an audit record and must not be editable).
- Never return stack traces or database errors to the client.

## Tests worth running (Member 6)

Try with Postman or Burp Suite against the real backend: customer token on `/cases`, no token on `/alerts`, a tampered token, a decision on a closed case, a 10 000-character report, and SQL/HTML characters in every text field.
