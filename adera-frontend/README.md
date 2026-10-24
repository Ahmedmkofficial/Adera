# Adera frontend

The React frontend for **Adera**, an explainable fraud-intelligence and investigation platform for digital payments (university project, Member 5: Frontend and Investigation Interface).

Everything is **simulated**. There are no real banks, no real money and only synthetic data.

## Two apps in one

| Side | Who | What they do |
|---|---|---|
| Customer (mobile layout) | `customer` accounts | Enter a recipient and amount, see the risk warning and *why*, cancel / verify / send, report suspicious activity |
| Analyst (desktop layout) | `analyst` accounts | See alerts, investigate a recipient, view related accounts and the relationship graph, open a case, record a decision |

## Quick start

```bash
npm install
npm run dev          # http://localhost:5173
```

It works with **no backend**: by default it answers from built-in demo data (`src/mock`).

### Accounts (built-in data mode)

| Role | Sign in with | Password |
|---|---|---|
| Admin (analyst) | username `admin` | `admin` |
| Customer | phone `0911000001` | `demo-customer-1` |

Customers sign in at `/login` with their **phone number**. Analysts and admins use the separate `/analyst/login` page with their provisioned username or phone number. Usernames are not case-sensitive. Each page rejects credentials for the other role.

> `admin` / `admin` is a default credential. It exists only in the built-in data and is **left out of the build** when `VITE_USE_MOCK=false`. A real backend must never ship it (see [docs/SECURITY.md](docs/SECURITY.md)).

### Demo recipients (for the payment check)

| Phone | Result |
|---|---|
| `0912345678` | Critical, score 75 (the project's demo recipient) |
| `0911111111` | High, 50 |
| `0922222222` | Moderate, 25 |
| any other number | Low, 10 |

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Start the app while you work |
| `npm test` | Run all tests |
| `npm run lint` | Check the code for mistakes |
| `npm run build` | Make the production build in `dist/` |
| `npm run preview` | Serve the production build locally |

## Connecting the real backend

Copy `.env.example` to `.env` and set:

```
VITE_USE_MOCK=false
VITE_API_URL=http://localhost:8000
```

Then restart `npm run dev`. Customers use `/login`; analysts and admins use `/analyst/login` with a staff phone number or a username assigned by a trusted operator. The backend's staff-username migration must be applied before using username login. All server calls live in **one file**, `src/services/api.js`, and follow [docs/API_CONTRACT.md](docs/API_CONTRACT.md). Pages never talk to the server directly, and the frontend never calculates risk: it only shows what the backend returns.

The light/dark preference is shared across customer and analyst screens and is saved in browser storage. The fingerprint-shield mark is reused by the app UI and SVG favicon.

For local development, configure the backend's `CORS_ALLOWED_ORIGINS` with the exact Vite origin if it differs from `http://localhost:5173` or `http://127.0.0.1:5173`.

## Folder map

```
src/
├── auth/          sign-in state, session storage, ProtectedRoute, role rules
├── components/
│   ├── admin/     analyst layout, tables, graph, charts
│   ├── customer/  customer page frame
│   ├── risk/      risk sheet, ruler, "thread" list, hold-to-send button
│   └── ui/        Button, Field, Segmented control
├── mock/          built-in data and accounts (replaced by the real API later)
├── pages/         one file per screen
├── services/      api.js (all calls), http.js (Axios), config.js
├── test/          automated tests
└── utils/         formatting, risk wording, graph layout
```

## Routes

| Address | Who | Screen |
|---|---|---|
| `/login`, `/register` | customers | Sign in, create account |
| `/analyst/login` | analysts/admins | Dedicated analyst sign in |
| `/`, `/report`, `/confirmation/:type` | signed in | Send money, report, receipt |
| `/admin` | analysts | Overview |
| `/admin/alerts`, `/admin/alerts/:id` | analysts | Alert list, investigation |
| `/admin/entities`, `/admin/entity/:phone` | analysts | Lookup, entity profile |
| `/admin/entity/:phone/graph` | analysts | Relationship graph |
| `/admin/cases`, `/admin/cases/:id` | analysts | Case list, case and decision |

A customer who opens `/admin` sees a "No access" page. This only controls what the screen shows: **the backend must enforce the same rule** (see [docs/SECURITY.md](docs/SECURITY.md)).

## Design system

Calm and monochrome until risk appears: **color means risk and nothing else.** The signature motif is "the thread", a hairline with small dots that joins reasons, timelines and the graph.

- Colors and fonts: `src/index.css` (`:root`). Fonts are self-hosted (Hanken Grotesk, JetBrains Mono, Noto Sans Ethiopic), so the app makes no outside requests.
- Risk colors have a lighter fill version and a darker text version, so risk words pass the WCAG AA contrast limit.
- Stylesheets are per area (`customer.css`, `admin.css`, `risk.css`...) with prefixed class names (`cu-`, `op-`, `rk-`, `iv-`, `ent-`, `cs-`, `gr-`) so they cannot collide.

## More documents

- [docs/API_CONTRACT.md](docs/API_CONTRACT.md): what the frontend expects from each endpoint
- [docs/SECURITY.md](docs/SECURITY.md): security decisions and what the backend must also do
- [docs/ACCESSIBILITY.md](docs/ACCESSIBILITY.md): what was checked and what to check by hand
- [docs/HANDOFF.md](docs/HANDOFF.md): copying this into the team repository

## Known limits

- Demo data resets when the page is refreshed.
- The sign-in token is kept in `sessionStorage` (see the security notes).
- Alert and case lists load everything at once; a real backend should page them.
- Screens are tested with automated tests and a structure check, not on real phones. Test on a real device before the demo.
