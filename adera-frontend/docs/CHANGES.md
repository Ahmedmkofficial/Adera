# What changed

## Current update: authentication, themes and branding

- **Username login**: real-backend staff login now sends the username field supported by the API; customer and legacy staff phone login still send `phone`. Applying the staff-username migration is required before assigning usernames. The built-in `admin` / `admin` credential remains demo-only.
- **Two visual identities**: customer screens use a reassuring payment-security look; analyst screens use a denser operations-console treatment. Both share responsive layout primitives and color tokens.
- **Light and dark themes**: the accessible toggle is shared across both interfaces, persists in browser storage, and initializes before app rendering to reduce theme flash.
- **Fingerprint-shield brand mark**: one reusable SVG mark is used in the application and as the SVG favicon/installable icon.
- **Motion and accessibility**: route entrance motion is defined centrally and honors reduced-motion preferences.
- **Tests**: see the current `npm test` output; older counts below describe the earlier design pass.

## Earlier: logo, admin sign-in and wording pass

- Previous logo and demo sign-in behavior are retained here as historical notes.
- **Prototype wording removed**: the "PROTOTYPE · SYNTHETIC DATA" tag, the sidebar version label, the "demo accounts" block on the sign-in page, and the "Demo ..." account names. A test (`wording.test.jsx`) fails if such wording comes back.
- The receipt keeps one honest line, "Simulated payment. No money was moved.", because the screen would otherwise say a payment was sent when no money moved.
- The sign-in and register pages now have a real `h1` heading.
- Tests: 87.

Compared with the project before this pass (customer pages, analyst pages and the graph on demo data).

# Earlier: finishing pass

## Added
- **Sign-in, roles and guards**: `src/auth/` (session, `AuthProvider`, `ProtectedRoute`, role rules). Customers can't open `/admin`; analysts and customers start in different places; "No access" page; sign-out; auto sign-out after 15 idle minutes or when the token expires or the server says 401.
- **Real Axios layer**: `src/services/http.js` (token header, 401 handling) and `src/services/api.js` with a one-setting switch between demo data and the real backend (`VITE_USE_MOCK`, `VITE_API_URL`, see `.env.example`).
- **Payment recording**: sending now calls `POST /transactions/simulate`, blocks double sends, and the receipt shows a reference (`TXN-...`), time and the risk level at that moment.
- **Demo accounts** (demo mode only) with "Fill customer / analyst" buttons on the sign-in page.
- **Tests** (`npm test`, 68): sign-in and roles, the payment flow, hold-to-send, reporting, alerts, investigation, entities, cases and decisions, the graph and its layout, the API layer against a fake server, utilities, and an accessibility structure check.
- **Docs**: README, API contract, security notes, accessibility notes, handoff steps.
- Browser tab titles per page, "Skip to content" link, focus moves to the new page after navigation.

## Fixed
- A screen-reader/structure check found: unlabeled sidebars (two "complementary" landmarks) and a skipped heading level on the case page.
- Risk colors used as text were too light (amber 2.8:1, orange 3.4:1). Text now uses darker twins that pass 4.5:1; fills and lines keep the brand colors.
- The "you were signed out" message was lost when two redirects raced. The reason now lives in the auth state.
- The count-up animation crashed in browsers without `matchMedia`.
- The graph page: removed the grid-dot background (the design says none) and the hidden React Flow attribution, restored the keyboard-reachable node list, fixed the lint errors.

- After sign-in, an analyst who first opened the plain address `/` was sent to the customer page. Analysts now always land in `/admin` unless they came from an `/admin` page.

## Cleaned up
- Removed Vite starter leftovers (`App.css`, `hero.png`, logos, `icons.svg`, `placeholder.jsx`), fixed the `ivestigation.css` file name, new favicon and page title, line endings set to LF (`.gitattributes`).
- Fonts are now installed with the project (`@fontsource/*`) instead of loaded from Google, so the app makes no outside requests and loads faster.
- The Investigation page reuses the shared transaction, report and related-account components instead of its own copies.
- The graph page loads only when opened, keeping the main bundle small.
- `npm run lint`, `npm test` and `npm run build` all pass; `npm audit` reports 0 vulnerabilities.
