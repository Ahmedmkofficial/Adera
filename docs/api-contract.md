# Adera API Contract

This document outlines the agreed API contracts for backend endpoints owned and co-developed across the team.

---

## 1. Alerts API (`backend/api/alerts.py`)
**Owner**: Tigiste (Member 6)  
**Security**: Requires authentication with role `ANALYST` or `ADMIN`.

### `GET /alerts`
Retrieve all alerts with optional status filtering.

- **Query Parameters**:
  - `status` (optional, string enum): `OPEN` | `INVESTIGATING` | `RESOLVED`
- **Headers**:
  - `Authorization`: `Bearer <token>`
- **Response `200 OK`**:
  ```json
  [
    {
      "id": 1042,
      "recipient_phone": "0912345678",
      "message": "Critical risk detected: multiple independent fraud reports",
      "severity": "CRITICAL",
      "status": "OPEN",
      "risk_score": 82
    }
  ]
  ```
- **Error Responses**:
  - `401 Unauthorized`: Missing or invalid token.
  - `403 Forbidden`: Authenticated user is not an `ANALYST` or `ADMIN`.

---

### `GET /alerts/{id}`
Retrieve a single alert's details for investigation.

- **Path Parameters**:
  - `id` (integer, required): Alert identifier.
- **Headers**:
  - `Authorization`: `Bearer <token>`
- **Response `200 OK`**:
  ```json
  {
    "id": 1042,
    "recipient_phone": "0912345678",
    "message": "Critical risk detected: multiple independent fraud reports",
    "severity": "CRITICAL",
    "status": "OPEN",
    "risk_score": 82
  }
  ```
- **Error Responses**:
  - `401 Unauthorized`: Missing or invalid token.
  - `403 Forbidden`: Authenticated user is not an `ANALYST` or `ADMIN`.
  - `404 Not Found`: Alert not found.

---

### `PATCH /alerts/{id}`
Update the status of an alert during an investigation.

- **Path Parameters**:
  - `id` (integer, required): Alert identifier.
- **Headers**:
  - `Authorization`: `Bearer <token>`
  - `Content-Type`: `application/json`
- **Request Body**:
  ```json
  {
    "status": "INVESTIGATING"
  }
  ```
  Allowed values: `"OPEN"`, `"INVESTIGATING"`, `"RESOLVED"`.
- **Response `200 OK`**:
  ```json
  {
    "id": 1042,
    "recipient_phone": "0912345678",
    "message": "Critical risk detected: multiple independent fraud reports",
    "severity": "CRITICAL",
    "status": "INVESTIGATING",
    "risk_score": 82
  }
  ```
- **Error Responses**:
  - `400 / 422 Unprocessable Entity`: Invalid status value.
  - `401 Unauthorized`: Missing or invalid token.
  - `403 Forbidden`: Access denied.
  - `404 Not Found`: Alert not found.

---

## 2. Cases API (`backend/api/cases.py`)
**Owner**: Tigiste & Ahmed  
**Security**: Requires authentication with role `ANALYST` or `ADMIN`.

### `GET /cases`
List scam/fraud investigation cases.

- **Query Parameters**:
  - `status` (optional, string)
- **Response `200 OK`**:
  ```json
  [
    {
      "id": 1021,
      "title": "Impersonation Scam on 0912345678",
      "description": "Multiple victims reported receiving urgent money transfer demands",
      "scam_type": "IMPERSONATION",
      "status": "OPEN",
      "decision": null,
      "notes": null
    }
  ]
  ```

---

### `POST /cases`
Create a new case from an alert or report.

- **Request Body**:
  ```json
  {
    "title": "Impersonation Scam on 0912345678",
    "description": "Multiple victims reported receiving urgent money transfer demands",
    "scam_type": "IMPERSONATION",
    "status": "OPEN"
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "id": 1021,
    "title": "Impersonation Scam on 0912345678",
    "description": "Multiple victims reported receiving urgent money transfer demands",
    "scam_type": "IMPERSONATION",
    "status": "OPEN",
    "decision": null,
    "notes": null
  }
  ```

---

### `GET /cases/{id}`
Retrieve details for a single case.

- **Path Parameters**:
  - `id` (integer, required): Case identifier.
- **Response `200 OK`**:
  ```json
  {
    "id": 1021,
    "title": "Impersonation Scam on 0912345678",
    "description": "Multiple victims reported receiving urgent money transfer demands",
    "scam_type": "IMPERSONATION",
    "status": "OPEN",
    "decision": null,
    "notes": null
  }
  ```
- **Error Responses**:
  - `404 Not Found`: Case not found.

---

### `POST /cases/{id}/decision`
Record an analyst's decision and conclusion on a case.

- **Path Parameters**:
  - `id` (integer, required): Case identifier.
- **Request Body**:
  ```json
  {
    "decision": "FRAUD",
    "notes": "Multiple independent reports and related scam activity support the case."
  }
  ```
  Allowed decisions: `"FRAUD"`, `"FALSE_POSITIVE"`, `"NEEDS_MORE_INFORMATION"`.
- **Response `200 OK`**:
  ```json
  {
    "case_id": 1021,
    "status": "RESOLVED",
    "decision": "FRAUD"
  }
  ```
- **Error Responses**:
  - `401 Unauthorized`: Missing authentication.
  - `403 Forbidden`: User is not an analyst/admin.
  - `404 Not Found`: Case not found.
  - `422 Unprocessable Entity`: Invalid decision type or missing/empty notes.
