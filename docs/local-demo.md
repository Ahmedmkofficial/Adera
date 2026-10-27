# Local Adera MVP demo

This demo uses a new SQLite file under `.local-demo/`, synthetic-only records,
and services bound to loopback. It does not use the repository `.env`, contact a
payment provider, or run Alembic migrations. Do not expose these services to a
network or use this setup for real users.

## Initialize once

From the repository root, run:

### Linux / macOS
```sh
.venv/bin/python scripts/init_local_demo.py
```

### Windows (PowerShell)
```powershell
.\.venv\Scripts\python.exe scripts\init_local_demo.py
```

The initializer refuses to replace an existing `.local-demo/adera-demo.sqlite3`
or `.local-demo/demo.env`. It builds tables from the current SQLAlchemy models,
creates a synthetic recipient `0912345678`, linked accounts, seven synthetic
reports, two synthetic cases, relationships, and one analyst. It prints a
random analyst password once; save it. The environment file is created with
owner-only permissions and contains a newly generated local JWT secret. The
script never imports the application settings module or reads `.env`.

If either generated file already exists, stop and use a separately reviewed
fresh local copy/path rather than deleting or overwriting it.

## Start FastAPI

In terminal 1, from the repository root:

### Linux / macOS
```sh
set -a
. .local-demo/demo.env
set +a
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### Windows (PowerShell)
```powershell
Get-Content .local-demo\demo.env | Where-Object { $_ -match '^([^=]+)=(.*)$' } | ForEach-Object { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) }
.\.venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000
```

## Start the React frontend

In terminal 2:

```sh
cd adera-frontend
npm run dev -- --host 127.0.0.1
```

Open the local Vite URL printed by the command (normally `http://127.0.0.1:5173`).
Vite proxies `/api/*` to `http://127.0.0.1:8000/*`, matching the FastAPI router
paths. Sign in with the analyst phone `0999000001` and the one-time password
printed by the initializer, then visit the analyst dashboard. Register a
separate regular user through the UI to use risk checks and submit reports.

For a demo risk check, enter recipient `0912345678` and an amount of `5000` ETB.
The existing risk endpoint requires a recipient user with a payment account;
the initializer creates both. Current backend counts, rules, and risk scores
remain unchanged. Risk checks at high/critical levels may create additional
alerts in this demo database.

## Expand an existing initialized demo

From the repository root, run this command to add synthetic dashboard scenarios
to the existing isolated database:

### Linux / macOS
```sh
.venv/bin/python scripts/expand_local_demo.py
```

### Windows (PowerShell)
```powershell
.\.venv\Scripts\python.exe scripts\expand_local_demo.py
```

The expansion is idempotent: rerunning it preserves existing rows and adds no
duplicate expansion reports, cases, assessments, or alerts. It verifies that
`.local-demo/demo.env` points exactly to `.local-demo/adera-demo.sqlite3`, checks
the SQLite file signature and actual connected SQLite path, and requires the
initialized synthetic recipient and analyst. It never reads the repository
`.env`, uses PostgreSQL, or invokes Alembic.

Expected totals after expansion of a freshly initialized demo are **13 payment
accounts, 24 fraud reports, 7 cases, 13 risk assessments, and 3 alerts**. If you
already checked risk or created demo records, those rows are preserved and
totals may be higher. Ten fictional recipient accounts and twenty reports are
added; cases, assessments, and alerts use existing model fields and scoring
services. Only HIGH/CRITICAL results create alerts under the current backend
contract; LOW and MODERATE results appear in risk assessments but do not create
alerts. The scenarios demonstrate all four risk levels without changing risk
rules: one recipient scores MODERATE, one HIGH, and the base and another
recipient score CRITICAL; remaining account-holders score LOW.

After expansion, start FastAPI and Vite using the commands above. Restart either
service if it was running before expansion so the processes are using the demo
database and current frontend bundle. The existing analyst dashboard shows
alerts and case details from the API; full per-signal scoring explanations are
not included in the current alert/case responses.

## Security notes

- Public registration always creates `USER`; privileged accounts are provisioned
  only by this local initializer or a trusted operator outside public signup.
- The `/admin/*`, `/alerts`, and `/cases` endpoints enforce analyst/admin roles.
- Stop both servers after the demo. `.local-demo/` is ignored by Git; do not
  publish its environment file or database.
- The initializer fails if its fixed database or config file already exists. It
  never overwrites an existing database.
