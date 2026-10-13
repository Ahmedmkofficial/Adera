# Adera database (data layer)

PostgreSQL + SQLAlchemy + Alembic. Git stores the **code**; every teammate runs
their **own local database** and builds it from the migrations below.

## Setup (once per machine)

1. Install and start PostgreSQL (Linux: `sudo systemctl start postgresql`).
2. Create the login and database:

   ```bash
   psql -U postgres -h localhost -c "CREATE USER adera_user WITH PASSWORD 'adera_dev_password';" -c "CREATE DATABASE adera_db OWNER adera_user;"
   ```

3. Create a `.env` file in the project root (it is git-ignored, never commit it):

   ```
   DATABASE_URL=postgresql://adera_user:adera_dev_password@localhost:5432/adera_db
   ```

4. Install packages and build the tables:

   ```bash
   python3 -m venv backend/.venv
   source backend/.venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   ```

5. Load the fictional demo data:

   ```bash
   python -m backend.database.seed
   ```

Check it worked: `psql -U adera_user -h localhost -d adera_db -c "\dt"` should
list 10 tables plus `alembic_version`.

> **Already have tables from an older setup?** Reset your local database
> (it only holds test data), then repeat steps 4 and 5:
>
> ```bash
> psql -U postgres -h localhost -c "DROP DATABASE adera_db;" -c "CREATE DATABASE adera_db OWNER adera_user;"
> ```

## Tables

| Table | Purpose |
|---|---|
| `users` | People who send money and file reports |
| `payment_accounts` | Payment accounts / recipients (has `phone_number`) |
| `transactions` | Simulated payments (`sender_id`, `recipient_phone`, `timestamp`) |
| `fraud_reports` | Reports from users (an observation, not proof of fraud) |
| `scam_cases` | Investigations; linked to reports and accounts |
| `scam_case_reports`, `scam_case_accounts` | Link tables for the case links |
| `account_relationships` | Connections between accounts (`SHARED_PHONE`, `SHARED_DEVICE`, `TRANSACTION`, `RELATED_ACCOUNT`) |
| `risk_assessments` | Risk history per recipient phone (`score`, `level`, `created_at`) |
| `alerts` | Alerts per recipient phone (`OPEN`, `UNDER_REVIEW`, `RESOLVED`) |

Reports, transactions, risk assessments and alerts are keyed by
`recipient_phone`. Accounts are connected to them by `payment_accounts.phone_number`.

## Query functions (for the API and the risk engine)

`backend/database/queries.py`. Every function takes an open session (`db`, from `get_db`).

| Function | Answers |
|---|---|
| `get_account_profile(db, identifier)` | Everything known about a phone or account number, as plain dicts |
| `count_reports(db, phone)` | How many fraud reports? |
| `count_recent_reports(db, phone, days=7)` | How many in the last N days? |
| `count_independent_reporters(db, phone)` | How many different people reported it? |
| `get_related_accounts(db, account_id)` | Which accounts are connected? |
| `get_transactions(db, phone)` | Payment history |
| `get_cases_for_phone(db, phone)` | Which scam cases involve it? |
| `get_risk_history(db, phone)` | Past risk assessments, oldest first |
| `has_open_alert(db, phone)` | Is there an `OPEN` alert? |

Example in FastAPI:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.database.queries import get_account_profile

@router.get("/intelligence/{identifier}")
def intelligence(identifier: str, db: Session = Depends(get_db)):
    return get_account_profile(db, identifier)
```

## Demo accounts

| Account | What it shows |
|---|---|
| `0912345678` | 7 reports from 7 people (5 in the last 7 days), 2 cases, 2 related accounts, risk 32 → 48 → 82 (CRITICAL), 1 open alert |
| `0923456789` | 0 reports, normal transactions, LOW risk |
| `0934567890` | 3 reports, receives money from `0912345678` (HIGH, alert under review) |
| `0945678901` | Related to `0912345678` (MODERATE) |
| `0956789012` | 3 reports from only 1 reporter (MODERATE) |
| `0967890123` | Fake investment group, 4 reports, shares a device with `0978901234` (HIGH, open alert) |
| `0989012345` | Ordinary shop (LOW) |

`python -m backend.database.seed --reset` wipes **all** rows and reloads the demo
data. Without `--reset` the script refuses to run on a database that has data.

## Changing the schema

Never edit tables by hand.

1. Change the model in `backend/models/`.
2. `alembic revision --autogenerate -m "describe the change"`
3. Open the new file in `backend/alembic/versions/` and check it.
4. `alembic upgrade head`
5. Commit the model and the migration together, and tell the team (especially
   whoever builds the API).

## Rules

- Fictional data only. Never put real customer or banking information in the database.
- A fraud report is an observation, not proof that someone is fraudulent.
