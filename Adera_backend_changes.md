# Walkthrough: Tigiste's Backend Implementation & Security Lead Work

**Role**: Tigiste (Member 6) — Backend Co-developer (30%), Integration & Security Lead  
**Branch**: `feature/backend-testing`

---

## 1. Overview of Accomplishments

All assigned backend responsibilities, endpoint implementations, service integrations, authentication/authorization stubs, and automated test suites have been built and verified.

### Endpoints Implemented & Verified
- `GET /alerts`: Retrieves all alerts (with optional `status` filtering and enriched `risk_score`).
- `GET /alerts/{id}`: Retrieves details for a single alert.
- `PATCH /alerts/{id}`: Updates alert status (`OPEN`, `INVESTIGATING`, `RESOLVED`).
- `GET /cases`: Retrieves all scam investigation cases.
- `POST /cases`: Creates a new investigation case.
- `GET /cases/{id}`: Retrieves details of a specific case.
- `POST /cases/{id}/decision`: Records analyst decision (`FRAUD`, `FALSE_POSITIVE`, `NEEDS_MORE_INFORMATION` + `notes`).

---

## 2. Changes Made

### Pydantic Schemas (`backend/schemas/`)
- [`alert.py`](file:///c:/Users/26tig/Development/Adera/backend/schemas/alert.py): Defined `AlertStatus` (`OPEN`, `INVESTIGATING`, `RESOLVED`), `AlertSeverity` (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`), `AlertStatusUpdate`, and `AlertResponse`.
- [`case.py`](file:///c:/Users/26tig/Development/Adera/backend/schemas/case.py): Defined `CaseDecisionType` (`FRAUD`, `FALSE_POSITIVE`, `NEEDS_MORE_INFORMATION`), `CaseCreate`, `CaseResponse`, `CaseDecisionRequest`, and `CaseDecisionResponse`.
- [`__init__.py`](file:///c:/Users/26tig/Development/Adera/backend/schemas/__init__.py): Exported all schemas.

### Auth & Security Stubs (`backend/api/`)
- [`dependencies.py`](file:///c:/Users/26tig/Development/Adera/backend/api/dependencies.py): Created a clean dependency stub for Ahmed's JWT auth (`get_current_user` and `require_role`). Enforces Bearer token presence, token expiration checks, and role permissions (`ANALYST`, `ADMIN`, `USER`).

### Service Layer (`backend/services/`)
- [`case_service.py`](file:///c:/Users/26tig/Development/Adera/backend/services/case_service.py): Implemented `CaseService` handling:
  - Alert retrieval and dynamic lookup of latest `risk_score` from `RiskAssessment`.
  - Alert status transitions.
  - Alert creation directly triggered from risk engine thresholds (`create_alert_from_risk`).
  - Case creation and lookup.
  - Decision recording with case status updates (`RESOLVED` for fraud/false positive, `INVESTIGATING` for needs more information) and in-memory decision audit log while waiting for DB schema updates from Reyyan.

### API Routers (`backend/api/`)
- [`alerts.py`](file:///c:/Users/26tig/Development/Adera/backend/api/alerts.py): Implemented `GET /alerts`, `GET /alerts/{id}`, and `PATCH /alerts/{id}`.
- [`cases.py`](file:///c:/Users/26tig/Development/Adera/backend/api/cases.py): Implemented `GET /cases`, `POST /cases`, `GET /cases/{id}`, and `POST /cases/{id}/decision`.

### Application Configuration (`backend/main.py`)
- [`main.py`](file:///c:/Users/26tig/Development/Adera/backend/main.py): Registered `alerts_router` and `cases_router`. Added `CORSMiddleware` so Getch's React frontend can communicate with the backend.

### Documentation (`docs/`)
- [`api-contract.md`](file:///c:/Users/26tig/Development/Adera/docs/api-contract.md): Fully documented endpoint contracts, request/response bodies, query params, and status codes for the frontend and team.

---

## 3. Test Suites & Validation Results

Implemented 36 tests across 5 test modules in `backend/tests/` using an in-memory SQLite database (`conftest.py`):

| Test Module | Coverage | Status |
| :--- | :--- | :--- |
| `test_alerts.py` | Empty state, populated with risk score, status filtering, single alert detail, 404s, PATCH valid status transitions, invalid enum rejection (422) | **8/8 PASSED** |
| `test_cases.py` | Empty state, case creation, case lookup, 404s, FRAUD / FALSE_POSITIVE / NEEDS_MORE_INFORMATION decisions, invalid decision (422), missing notes (422) | **10/10 PASSED** |
| `test_auth.py` | Missing token (401), invalid format (401), expired token (401), broken access control for standard USER (403), ANALYST and ADMIN allowed (200) | **11/11 PASSED** |
| `test_integration.py` | Full E2E flow: Risk assessment -> Alert creation -> Analyst alerts fetch -> Status to INVESTIGATING -> Case creation -> Decision submission (FRAUD) -> Case RESOLVED & stored | **1/1 PASSED** |
| `test_security.py` | SQL injection in path params, SQL injection in query params, SQL injection payloads in JSON body, empty field validation, direct object reference without auth | **6/6 PASSED** |

### Test Execution Output
```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\26tig\Development\Adera
plugins: anyio-4.15.1
collected 36 items

backend\tests\test_alerts.py ........                                    [ 22%]
backend\tests\test_auth.py ...........                                   [ 52%]
backend\tests\test_cases.py ..........                                   [ 80%]
backend\tests\test_integration.py .                                      [ 83%]
backend\tests\test_security.py ......                                    [100%]

======================= 36 passed, 9 warnings in 0.88s ========================
```

---

## 4. Definition of Done Checklist

- [x] **APIs work**: `GET /alerts`, `GET /alerts/{id}`, `PATCH /alerts/{id}`, `GET /cases`, `POST /cases`, `GET /cases/{id}`, `POST /cases/{id}/decision`.
- [x] **Invalid input is rejected**: Enum validation rejects invalid status or decision with HTTP 422; missing notes rejected with HTTP 422.
- [x] **Authentication works**: Missing or malformed tokens return HTTP 401.
- [x] **Authorization works**: Role verification checks permissions.
- [x] **Analyst endpoints are protected**: Normal `USER` role is rejected with HTTP 403 Forbidden on all analyst endpoints (Broken Access Control prevention).
- [x] **React can communicate with the API**: CORS headers enabled on FastAPI.
- [x] **Risk Engine results become alerts**: `CaseService.create_alert_from_risk` transforms high/critical risk into alerts.
- [x] **Cases can be investigated**: Full lifecycle tested from open alert to investigation case.
- [x] **Decisions are stored**: Case decisions (`FRAUD`, `FALSE_POSITIVE`, `NEEDS_MORE_INFORMATION`) and notes are stored and case status is updated to `RESOLVED` / `INVESTIGATING`.

---

## 5. Team Coordination & Next Steps

### Blockers / Requests for Team Members:
1. **For Ahmed (70% Backend / Auth Lead)**:
   - When your JWT authentication is ready, simply replace the token lookup inside `backend/api/dependencies.py`. All route signatures and role dependency calls (`require_role(["ANALYST", "ADMIN"])`) will continue working without modification.
2. **For Reyyan (Database Lead)**:
   - In `backend/models/alert.py`: Add `risk_score: Mapped[Optional[int]] = mapped_column(nullable=True)` to `Alert` table. (Our service currently enriches this from `RiskAssessment` seamlessly).
   - In `backend/models/scam_case.py`: Add `decision: Mapped[Optional[str]]` and `notes: Mapped[Optional[str]]` columns. (Our service currently caches them in an audit store).
   - In `backend/models/user.py`: Add `role: Mapped[str] = mapped_column(String(20), default="USER")`.
