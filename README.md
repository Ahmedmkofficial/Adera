# ADERA

## Explainable Fraud Intelligence & Investigation Platform

Adera is a fraud-intelligence and investigation platform designed to detect and analyze suspicious digital-payment activity, especially **social-engineering and payment scams**.

Instead of only giving a transaction a risk score, Adera connects:

```text
Payment Activity
       ↓
Fraud Intelligence
       ↓
Entities & Relationships
       ↓
Risk Analysis
       ↓
Alert
       ↓
Investigation
       ↓
Case
       ↓
Analyst Decision
```

The project is a **university proof of concept** using synthetic data and a simulated payment environment.

It does not connect to real banks, real payment providers, or real customer accounts.

---

# 1. Project Goal

The goal of Adera is to demonstrate how fraud intelligence can help identify suspicious recipients and payment activity before or during a simulated transaction.

Adera focuses on:

* Social-engineering scams
* Recipient risk
* Fraud reports
* Connected entities
* Suspicious relationships
* Explainable risk scoring
* Fraud alerts
* Analyst investigations
* Fraud cases
* Analyst decisions

The project is inspired by concepts used in modern fraud-management and investigation platforms, but is intentionally much smaller and designed for a university MVP.

---

# 2. Main Workflow

The core Adera workflow is:

```text
User initiates payment
        ↓
Recipient identified
        ↓
Fraud intelligence retrieved
        ↓
Related entities and relationships checked
        ↓
Risk Engine evaluates signals
        ↓
Risk Assessment generated
        ↓
Alert created if necessary
        ↓
Analyst investigates
        ↓
Case created
        ↓
Analyst records decision
```

Possible analyst decisions:

```text
FRAUD
FALSE_POSITIVE
NEEDS_MORE_INFORMATION
```

---

# 3. Main Features

## Customer Payment Interface

The user can simulate a payment by entering:

```text
Recipient
Amount
```

Adera checks the recipient and displays:

```text
Risk Score
Risk Level
Risk Reasons
Recommendation
```

Example:

```text
Risk Score: 82/100

Level: CRITICAL

Reasons:
• Multiple independent fraud reports
• Recent fraud reports
• Previous scam cases
• Suspicious account relationship
• Repeated scam pattern

Recommendation:
STOP_AND_VERIFY
```

---

## Fraud Reporting

Users can report suspicious recipients.

A report contains information such as:

```text
Recipient
Scam Type
Description
Reporter
Timestamp
```

A report is treated as an **observation**, not automatic proof that someone is committing fraud.

Multiple independent reports and supporting evidence can increase confidence.

---

## Fraud Intelligence

Adera connects information from multiple sources, including:

```text
Fraud Reports
Transactions
Scam Cases
Risk Assessments
Account Relationships
Historical Activity
```

This allows analysts to investigate connections instead of looking at isolated transactions.

---

## Entity Relationships

Adera represents relationships between accounts.

Example:

```text
Account A
    │
    ├── SHARED_PHONE ──→ Account B
    │
    ├── TRANSACTION ──→ Account C
    │
    └── RELATED_ACCOUNT ──→ Account D
```

Relationships are stored in PostgreSQL.

The frontend can display these relationships as a graph.

---

## Risk Engine

Adera uses an explainable rule-based Risk Engine for the MVP.

Example signals include:

```text
Multiple independent reports
Recent reports
Previous scam cases
Suspicious relationships
Repeated scam patterns
Unusual transaction behavior
```

Initial scoring model:

```text
Multiple independent reports       +20
Recent reports                     +15
Previous scam case                 +25
Suspicious relationship            +15
Repeated scam pattern              +10
Unusual transaction behavior       +10
```

The final score is capped at:

```text
100
```

Risk levels:

```text
0–24     LOW
25–49    MODERATE
50–74    HIGH
75–100   CRITICAL
```

Recommendations:

```text
LOW         → ALLOW
MODERATE    → REVIEW
HIGH        → VERIFY
CRITICAL    → STOP_AND_VERIFY
```

These are initial engineering rules for the prototype and are not claims of real-world fraud accuracy.

---

# 4. Example Risk Input

The Risk Engine can receive information such as:

```python
risk_input = {
    "transaction_amount": 5000,
    "independent_reports": 7,
    "recent_reports": 3,
    "previous_scam_cases": 2,
    "suspicious_relationships": 1,
    "repeated_scam_pattern": True,
    "unusual_transaction": True
}
```

Example output:

```python
{
    "score": 82,
    "level": "CRITICAL",
    "recommendation": "STOP_AND_VERIFY",
    "reasons": [
        "Multiple independent fraud reports",
        "Recent fraud reports exist",
        "Previous scam case exists",
        "Suspicious account relationship detected",
        "Repeated scam pattern detected",
        "Unusual transaction behavior detected"
    ]
}
```

The system explains **why** the risk assessment was produced.

---

# 5. Investigation Center

Adera includes an analyst interface for investigating suspicious activity.

An analyst can view:

```text
Alerts
Recipients
Accounts
Transactions
Fraud Reports
Scam Cases
Risk History
Related Accounts
Relationships
```

The investigation process is:

```text
Alert
  ↓
Entity Profile
  ↓
Relationships
  ↓
Evidence
  ↓
Case
  ↓
Analyst Decision
```

The purpose is to demonstrate how connected fraud information can support an investigation.

---

# 6. Database

Adera uses:

**PostgreSQL**

Main entities:

```text
users
accounts
transactions
fraud_reports
scam_cases
account_relationships
risk_assessments
alerts
```

Important relationship table:

```text
account_relationships
```

Example:

```text
id
source_account_id
target_account_id
relationship_type
created_at
```

Relationship types include:

```text
SHARED_PHONE
SHARED_DEVICE
TRANSACTION
RELATED_ACCOUNT
```

All project data is synthetic.

No real banking or customer information is used.

---

# 7. Technology Stack

## Frontend

```text
React
Vite
JavaScript / TypeScript
Tailwind CSS
Axios
React Router
React Flow
```

## Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy
JWT
```

## Database

```text
PostgreSQL
Alembic
```

## Risk Engine

```text
Python
Rule-based scoring
Pytest
```

## Security & Testing

```text
Pytest
Postman
Burp Suite
OWASP ZAP
```

## Development

```text
Git
GitHub
Docker
Docker Compose
VS Code
```

---

# 8. Project Structure

```text
adera/
│
├── backend/
│   ├── api/
│   ├── auth/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── tests/
│
├── adera-frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       └── services/
│
├── data/
│   ├── scam_taxonomy.json
│   ├── fraud_indicators.json
│   ├── synthetic_reports.json
│   └── synthetic_scam_cases.json
│
├── docs/
│
├── tests/
│
├── alembic.ini
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 9. API

The main risk endpoint is:

```text
POST /risk/check
```

Request:

```json
{
  "recipient_phone": "0912345678",
  "amount": 5000
}
```

Response:

```json
{
  "score": 82,
  "level": "CRITICAL",
  "recommendation": "STOP_AND_VERIFY",
  "reasons": [
    "Multiple independent fraud reports",
    "Recent fraud reports exist",
    "Previous scam case exists"
  ]
}
```

Other endpoints include:

```text
POST /auth/register
POST /auth/login

POST /risk/check

POST /transactions/simulate
GET  /transactions/{id}

POST /reports
GET  /reports

GET  /recipients/{phone}

GET  /alerts
GET  /alerts/{id}
PATCH /alerts/{id}

GET  /cases
POST /cases
GET  /cases/{id}

POST /cases/{id}/decision
```

---

# 10. Backend Architecture

```text
                 React Frontend
                       │
                       ▼
                 FastAPI Backend
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     PostgreSQL    Risk Engine    Auth
          │            │
          └──────┬─────┘
                 ▼
          Risk Assessment
                 │
                 ▼
               Alert
                 │
                 ▼
          Investigation
                 │
                 ▼
               Case
                 │
                 ▼
          Analyst Decision
```

---

# 11. Team

Adera is being developed by six team members.

| Member             | Responsibility                                |
| ------------------ | --------------------------------------------- |
| Member 1 — Biruk   | Threat Intelligence                           |
| Member 2 — Kassu   | Risk Engine & Detection                       |
| Member 3 — Reyyan  | Database & Fraud Intelligence                 |
| Member 4 — Ahmed   | Backend & API — 70%                           |
| Member 5 — Getch   | Frontend & Investigation Interface            |
| Member 6 — Tigiste | Backend — 30%, Alerts, Integration & Security |

The backend is shared between Ahmed and Tigiste.

```text
Ahmed     → approximately 70%
Tigiste   → approximately 30%
```

Tigiste is a backend co-developer, not only a tester.

---

# 12. GitHub Workflow

The project uses one shared GitHub repository.

Repository:

```text
adera
```

Branches:

```text
main
develop

feature/threat-intelligence
feature/risk-engine
feature/database
feature/backend
feature/frontend
feature/backend-testing
```

Workflow:

```text
Feature Branch
      ↓
Pull Request
      ↓
develop
      ↓
Integration Testing
      ↓
main
```

Nobody should directly push to `main`.

The feature branches are used for individual development.

`develop` is the shared integration branch.

`main` contains the stable project.

---

# 13. Development Rules

The team follows these rules:

### 1. Use the shared repository

Do not create separate repositories for each member.

### 2. Use feature branches

Do not develop directly on `main`.

### 3. Use Pull Requests

Completed work should go through a Pull Request before entering `develop`.

### 4. Keep API contracts stable

Frontend and backend development depend on agreed request/response formats.

### 5. Use mock data when necessary

Members should not wait for another component to be completed before starting.

### 6. Use synthetic data

Do not use real banking records or customer information.

### 7. Do not commit secrets

Never commit:

```text
.env
passwords
API keys
private credentials
```

### 8. Test before merging

Code should be tested before it is merged into the shared development branch.

---

# 14. Security

Adera is designed as a defensive cybersecurity project.

Security areas include:

```text
Authentication
Authorization
Input validation
Password hashing
JWT security
SQL injection prevention
Sensitive information protection
API abuse
Error handling
Role-based access control
```

Roles:

```text
USER
ANALYST
ADMIN
```

The backend enforces authorization.

The frontend must never be trusted to enforce permissions by itself.

---

# 15. Synthetic Data

Adera does not use real banking data.

The project uses fictional:

```text
Users
Accounts
Phone numbers
Transactions
Fraud reports
Scam cases
Relationships
Risk assessments
Alerts
```

The synthetic data is designed to demonstrate different situations:

```text
LOW RISK
MODERATE RISK
HIGH RISK
CRITICAL RISK
FALSE POSITIVE
```

---

# 16. MVP Scope

The MVP focuses on one complete investigation workflow:

```text
Payment
   ↓
Recipient Intelligence
   ↓
Relationship Analysis
   ↓
Risk Assessment
   ↓
Alert
   ↓
Investigation
   ↓
Case
   ↓
Analyst Decision
```

The team will prioritize making this workflow work end-to-end before adding optional features.

---

# 17. Out of Scope

The MVP does **not** include:

```text
Real CBE integration
Real Telebirr integration
Real bank databases
Real customer information
Real-money transactions
Automatic account freezing
Automatic accusations
National fraud database
Large-scale AI/ML models
Every possible fraud type
Neo4j
Enterprise-scale infrastructure
```

Adera is a proof of concept, not a production banking security system.

---

# 18. Final Demonstration

The final demonstration should tell one complete story.

A user receives a suspicious message:

```text
"Please send 5,000 ETB urgently to 0912345678."
```

The user opens the simulated payment application.

They enter:

```text
Recipient:
0912345678

Amount:
5,000 ETB
```

Adera checks the recipient.

The system finds:

```text
Multiple fraud reports
Recent reports
Related accounts
Previous scam cases
Suspicious activity
```

The Risk Engine produces:

```text
82 / 100
CRITICAL
```

The user sees:

```text
ADERA SECURITY WARNING

This recipient has multiple risk indicators.

Risk Score: 82/100

Recommendation:
STOP AND VERIFY
```

The user can cancel or verify the payment.

The analyst then opens the Adera Investigation Center.

The analyst sees:

```text
Alert
   ↓
Recipient
   ↓
Related Accounts
   ↓
Transactions
   ↓
Fraud Reports
   ↓
Previous Cases
   ↓
Evidence
```

The analyst creates or opens a case and records a decision.

This demonstrates:

**Detect → Connect → Score → Alert → Investigate → Decide**

---

# 19. Core Principle

Adera is not simply:

> "A website that gives a fraud score."

It is a small **fraud-intelligence and investigation platform**.

The important idea is that suspicious activity becomes more understandable when different pieces of information are connected:

```text
Transactions
+
Fraud Reports
+
Accounts
+
Relationships
+
Scam Cases
+
Risk Signals
+
Alerts
+
Analyst Decisions
```

The project demonstrates how these connected signals can help analysts investigate potential payment fraud while giving users understandable warnings.

---

# 20. Definition of Done

The MVP is considered complete when the team can demonstrate:

```text
1. User enters a recipient.
        ↓
2. User enters an amount.
        ↓
3. Adera checks the recipient.
        ↓
4. Backend retrieves fraud intelligence.
        ↓
5. Related entities are identified.
        ↓
6. Risk Engine evaluates the signals.
        ↓
7. Risk Assessment is generated.
        ↓
8. Alert is created when appropriate.
        ↓
9. User receives an understandable warning.
        ↓
10. Analyst investigates the alert.
        ↓
11. Analyst views related entities and evidence.
        ↓
12. Analyst creates/opens a case.
        ↓
13. Analyst records a decision.
        ↓
14. Security and integration tests pass.
```

The priority is a working end-to-end system rather than a large number of unfinished features.
