# Safe Alembic migration verification

## What changed

The root revision now creates the original application tables; later revisions add
only their incremental fields and relationship table. The Batch 4 revision no
longer re-adds `scam_cases.scam_type`. Temporary server defaults used to backfill
existing rows are removed after their columns are populated, matching the models'
Python-side defaults. `backend/alembic/env.py` honors an explicitly supplied
`DATABASE_URL`; the configured `alembic.ini` default remains unchanged.

**This migration repair is for a fresh database only. Do not run these upgrade
commands against `adera_db`.** That database is recorded at revision
`9a3873193da9` but already contains application schema; it requires separate,
read-only schema comparison and reconciliation planning before any future
migration action. The backup at `$HOME/adera_db_before_migration_repair.dump` is
not needed by these verification steps and must be retained.

## Fresh PostgreSQL database verification

Run from the repository root. This creates only the separate
`adera_dev_clean` database, connecting through PostgreSQL's maintenance database
`postgres` (not `adera_db`). It does not drop or alter any existing database.
The command intentionally fails safely if `adera_dev_clean` already exists; do
not replace it with a drop/reset command.

```sh
cd ~/Projects/adera
set -a
. ./.env
set +a
CLEAN_DATABASE_URL="${DATABASE_URL%/adera_db}/adera_dev_clean"
psql "${CLEAN_DATABASE_URL%/adera_dev_clean}/postgres" -v ON_ERROR_STOP=1 -c 'CREATE DATABASE adera_dev_clean OWNER adera_user TEMPLATE template0'
```

The following command applies the migration chain to `adera_dev_clean` only. The
environment URL takes precedence over the unchanged URL in `alembic.ini`:

```sh
DATABASE_URL="$CLEAN_DATABASE_URL" backend/.venv/bin/alembic -c alembic.ini upgrade head
```

Confirm the recorded revision:

```sh
DATABASE_URL="$CLEAN_DATABASE_URL" backend/.venv/bin/alembic -c alembic.ini current
```

## Application startup and schema smoke check

This imports the FastAPI application, opens a connection using the clean URL,
and confirms all eight model tables exist. It does not create or alter schema:

```sh
DATABASE_URL="$CLEAN_DATABASE_URL" backend/.venv/bin/python -c 'from sqlalchemy import inspect; from backend.database.session import engine; from backend.main import app; expected={"users", "payment_accounts", "fraud_reports", "transactions", "risk_assessments", "alerts", "scam_cases", "account_relationships"}; actual=set(inspect(engine).get_table_names()); assert expected <= actual, f"Missing tables: {expected - actual}"; print(f"{app.title} startup ok; migrated tables: {len(actual)}")'
```

## Automated tests

Run application tests with an isolated in-memory SQLite URL so the test modules'
existing `drop_all` setup cannot point at a PostgreSQL database:

```sh
DATABASE_URL=sqlite:// backend/.venv/bin/pytest -q
```

`backend/tests/test_migrations.py` renders the full PostgreSQL migration chain
in offline SQL mode. It verifies there is one Alembic head, all expected tables
are generated, the key foreign keys are emitted, and `scam_type` is not added a
second time. This offline test does not connect to PostgreSQL; the commands above
are the live fresh-database and application-startup verification.
