# Adera

Adera is a fraud-intelligence and recipient-risk prototype for digital payments.

The system checks a payment recipient against available fraud intelligence, produces an explainable risk assessment, and provides an analyst interface for reviewing reports and alerts.

> **Important:** Adera is a prototype. It does not connect to CBE, Telebirr, real banks, real customer data, or real-money payment systems.

---

# Project Structure

```text
adera/
│
├── frontend/              # React frontend
├── backend/               # FastAPI backend
│   ├── api/
│   ├── auth/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── tests/
│
├── data/                  # Synthetic fraud/scam data
├── tests/                 # Integration/security tests
├── docs/                  # Project documentation
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

# Team Branches

Everyone works in the same GitHub repository.

```text
main
  │
  └── develop
       │
       ├── feature/threat-intelligence
       ├── feature/risk-engine
       ├── feature/database
       ├── feature/backend
       ├── feature/frontend
       └── feature/backend-testing
```

## Branch assignments

| Member   | Branch                        | Main responsibility                        |
| -------- | ----------------------------- | ------------------------------------------ |
| Member 1 | `feature/threat-intelligence` | Scam intelligence and synthetic fraud data |
| Member 2 | `feature/risk-engine`         | Risk scoring and explanations              |
| Member 3 | `feature/database`            | PostgreSQL database and models             |
| Member 4 | `feature/backend`             | FastAPI backend and API                    |
| Member 5 | `feature/frontend`            | React frontend                             |
| Member 6 | `feature/backend-testing`     | Testing, security and backend support      |

Do not work directly on `main`.

Completed work should go through a Pull Request into `develop`.

---

# Backend Setup

## Requirements

Install:

* Python 3
* PostgreSQL
* Node.js and npm
* Git

---

## 1. Clone the repository

```bash
git clone https://github.com/Ahmedmkofficial/adera.git
cd adera
```

---

## 2. Create the Python virtual environment

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
```

---

## 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

---

# PostgreSQL Setup

Create a PostgreSQL user and database for local development.

Example:

```text
Database: adera_db
User: adera_user
```

The exact password is local to each developer.

---

# Environment Configuration

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://adera_user:your_password@localhost:5432/adera_db
```

Do not commit `.env`.

Use `.env.example` as the template.

---

# Database Migrations

After configuring PostgreSQL:

```bash
alembic upgrade head
```

To check whether the database schema matches the models:

```bash
alembic check
```

---

# Start the Backend

From the project root:

```bash
source backend/.venv/bin/activate
uvicorn backend.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

# Current API

## Risk

```text
POST /risk/check
```

Example request:

```json
{
  "recipient_phone": "0912345678",
  "amount": 5000
}
```

---

## Fraud Reports

```text
POST /reports
```

---

## Payment Simulation

```text
POST /transactions/simulate
```

---

## Admin

```text
GET /admin/reports
GET /admin/high-risk
GET /admin/alerts
```

The admin endpoints are currently basic development endpoints. Authentication and authorization will be developed further as part of the project.

---

# Frontend Setup

Open another terminal.

From the project root:

```bash
cd frontend
npm install
npm run dev
```

Vite will provide the local frontend address in the terminal.

---

# Development Workflow

Before starting new work:

```bash
git checkout develop
git pull origin develop
```

Then switch to your assigned feature branch:

```bash
git checkout feature/your-branch
```

Work on your assigned feature.

Check your changes:

```bash
git status
```

Commit:

```bash
git add .
git commit -m "Describe your change"
```

Push:

```bash
git push origin feature/your-branch
```

Then open a Pull Request:

```text
feature/your-branch → develop
```

---

# Pull Request Rules

Before opening a Pull Request:

1. Test your changes.
2. Make sure the application still starts.
3. Keep commits focused.
4. Explain what you changed.
5. Mention anything another teammate needs to know.

Do not directly push to `main`.

The `main` branch is reserved for the stable project.

---

# Working in Parallel

The team should use mock data when another component is not ready.

For example, the frontend can temporarily use:

```json
{
  "score": 82,
  "level": "CRITICAL",
  "recommendation": "STOP_AND_VERIFY",
  "reasons": [
    "Multiple users reported this recipient",
    "Recent fraud reports exist"
  ]
}
```

This allows frontend, backend, database and risk-engine development to happen simultaneously.

---

# Risk Levels

The current MVP uses:

```text
0–24     LOW
25–49    MODERATE
50–74    HIGH
75–100   CRITICAL
```

The risk engine should provide an explanation for its result rather than returning only a number.

Example:

```text
Score: 55
Level: HIGH

Reasons:
- Multiple independent fraud reports
- Related scam cases detected
```

---

# Important MVP Boundary

Adera does NOT currently include:

* Real CBE integration
* Real Telebirr integration
* Real bank databases
* Real customer information
* Real-money transactions
* Automatic account freezing
* Automatic accusations
* National fraud database
* Large AI/ML model
* Every possible fraud type
* Neo4j

The project uses synthetic data for demonstration and testing.

---

# Main Demonstration

The final MVP should demonstrate:

```text
User enters recipient
        ↓
User enters amount
        ↓
Adera checks recipient
        ↓
Backend retrieves fraud intelligence
        ↓
Risk Engine calculates risk
        ↓
Risk explanation is generated
        ↓
User receives warning
        ↓
Fraud report can be submitted
        ↓
Analyst can investigate reports/alerts
```

The main idea is:

> **Detect → Score → Explain → Respond → Investigate**

---

# Team Rule

The goal is not for six people to build six separate projects.

The goal is to build **one Adera system with six coordinated components**.

Use the shared repository, communicate before changing shared files, and keep `develop` working.
