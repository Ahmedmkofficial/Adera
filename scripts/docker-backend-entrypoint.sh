#!/usr/bin/env sh
set -e

# Run safe database migration up to head
echo "Running safe database migrations..."
alembic upgrade head

# Exec uvicorn server so process signals (SIGTERM/SIGINT) propagate cleanly
echo "Starting Adera API server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
