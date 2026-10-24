# API contract (verified frontend/backend integration)

Items marked **(implemented)** have a backend route and response shape verified in this repository. Items marked **(proposed)** still need backend implementation or agreement.

General rules:

- JSON in, JSON out. Base URL from `VITE_API_URL`.
- The backend must allow the exact frontend origin in `CORS_ALLOWED_ORIGINS`; local Vite defaults are `http://localhost:5173` and `http://127.0.0.1:5173`.
- Signed-in requests carry `Authorization: Bearer <token>`.
- Status codes the frontend understands: `401` = not signed in or session ended, `403` = signed in but not allowed, `404` = not found (shown as "not found" pages), `409` = already exists, `422` = invalid input.
- Scores are whole numbers 0 to 100. Levels: `LOW` 0-24, `MODERATE` 25-49, `HIGH` 50-74, `CRITICAL` 75-100.
- Recommendations: `ALLOW`, `REVIEW`, `VERIFY`, `STOP_AND_VERIFY`.
- The backend currently creates alerts for `HIGH` and `CRITICAL` risk checks.
- Roles: `customer`, `analyst`. **Analyst-only endpoints must reject customers with 403.**

## Authentication

| Call | Body | Response |
|---|---|---|
| `POST /auth/register` **(implemented)** | `{phone, name, password}` | `201` with `{id, phone, username, name, role}`; new accounts have `username: null` and role `USER`. `400` if the phone exists. |
| `POST /auth/login` **(implemented)** | Customer or existing staff phone: `{phone, password}`. Provisioned staff username: `{username, password}`. | `{access_token, token_type, user: {id, phone, username, name, role}}`. `401` for invalid credentials. Username lookup is case-insensitive; phone login remains supported. |

The staff `username` field is nullable and unique without regard to case. Public registration continues to create `USER` accounts and cannot select a username or privileged role. Existing analyst/admin accounts can continue using their phone number; a trusted operator must provision a username before that account can sign in by username. Apply the new Alembic migration before deploying this login contract.

If `user` is missing, the frontend uses `sub` as a fallback identifier and reads `name`, `role` and `exp` from token claims. `exp` is used only to end the screen session on time; the server must check it too.

## Customer

| Call | Body | Response |
|---|---|---|
| `POST /risk/check` **(PDF)** | `{recipient_phone, amount}` | `{score, level, recommendation, reasons: [string]}` |
| `POST /transactions/simulate` **(PDF)** | `{recipient_phone, amount}` | `{id, status: "SIMULATED", created_at}`. The receipt shows `TXN-<id>`. |
| `POST /reports` **(implemented)** | `{recipient_phone, scam_type, description}` | Currently returns `200` with the persisted report. The backend schema governs accepted scam types and description validation. |

## Analyst/admin endpoints (require role `ANALYST` or `ADMIN`)

| Call | Response |
|---|---|
| `GET /dashboard/summary` **(implemented)** | `{alerts, critical, high, open_cases, reports}`. `alerts` counts all alert records; `critical` and `high` count alerts by severity; `open_cases` counts `OPEN` and `INVESTIGATING` cases; `reports` counts all fraud reports. |
| `GET /alerts` **(implemented)** | Backend returns `{id, recipient_phone, severity, status, risk_score, risk_level, message, created_at}` rows. The frontend maps `risk_score`/`risk_level`/`message` to `score`/`level`/`reason`; maps `INVESTIGATING` to `IN_CASE` and `RESOLVED`/`DISMISSED` to `CLOSED`. Missing risk scores remain unavailable, not zero. |
| `GET /alerts/{id}` **(implemented)** | Backend returns nested `alert` and `risk_assessment` records plus persisted `reasons`, `transactions`, `reports`, `reports_total`, `related_accounts`, and `case_id`. Transaction counterparties identify the stored sender. `404` if unknown. |
| `PATCH /alerts/{id}` **(implemented)** | Body `{status}`; accepts backend statuses `OPEN`, `INVESTIGATING`, `RESOLVED`, `DISMISSED`. The frontend maps `IN_CASE` to `INVESTIGATING` and `CLOSED` to `RESOLVED`. Analyst/admin only. |
| `GET /recipients/{phone}` **(implemented, compact response)** | Returns `{phone, risk_score, risk_level, fraud_report_count, independent_reporter_count, recent_report_count, previous_scam_case_count, suspicious_relationship_count}`. Analyst/admin only; `404` if the recipient user does not exist. The frontend maps these persisted risk/intelligence fields and explicitly indicates when detail fields (reports, transactions, risk history, and cases) are not supplied by this endpoint. |
| `GET /recipients/{phone}/graph` **(implemented)** | Analyst/admin only. `{phone, reports_total, nodes: [...], edges: [{id, source, target, type}]}`. Node kinds: `subject`, `account` (`id, phone, level, score, report_count, last_activity`), `report` (`id, report_id, created_at, scam_type, summary`). `REPORT` edges refer to persisted fraud reports; account edges come only from persisted account relationships or transactions. `404` if the recipient user does not exist. Existing recipients with no related records return a subject-only graph. |
| `GET /cases` **(implemented)** | Rows include `{id, title, status, recipient_phone, alert_id, score, level, decision, created_at, updated_at}`. Frontend maps subject to `recipient_phone`, maps status to `OPEN`/`CLOSED`, and treats unavailable scores as unavailable. |
| `GET /cases/{id}` **(implemented)** | Returns the original nested case/evidence records plus frontend fields `subject`, `score`, `level`, `recommendation`, normalized source `status`, `decision`, `decided_by`, `decided_at`, `created_at`, `updated_at`, `events`, `evidence`, and `payment`. Missing decision timestamps and payments are returned as unavailable; the current model does not persist a decision timestamp. `404` if unknown. |
| `POST /cases` **(implemented)** | Accepts `{alert_id}` when the selected persisted alert has a non-empty message; that recorded message is used as both title and description. Explicit `title` and `description` remain accepted. Missing alert context is rejected with a validation error rather than fabricated text. Creating a case marks its alert `INVESTIGATING`. |
| `POST /cases/{id}/decision` **(implemented)** | Body `{decision}` with `FRAUD`, `FALSE_POSITIVE`, or `NEEDS_MORE_INFORMATION`. Final decisions set the case and alert to `RESOLVED`; more-information keeps both in `INVESTIGATING`. The frontend reloads case detail after recording a decision. |

### Decision rules the screens assume

- Backend stores final decisions as case/alert status `RESOLVED`; frontend displays them as `CLOSED`.
- `NEEDS_MORE_INFORMATION` keeps the case and alert `INVESTIGATING`; frontend displays the case as `OPEN` and alert as `IN_CASE`.
- The case stores the analyst id, but not a decision timestamp. The API does not invent that timestamp.

## Open questions for the team

1. What does "recent" mean for `recent_reports` (how many days)?
2. What is the shared value behind a `SHARED_PHONE` relationship? The graph can show it if it is returned.
3. Is `scam_cases` (a count on the profile) the same data as the profile's `cases` list?
4. Do `transactions[].counterparty` always mean the sender?
