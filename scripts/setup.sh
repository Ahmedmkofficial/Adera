#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== Adera setup: Linux / macOS ==="

# Validate repository files before installing anything.
for file in .env.example requirements.txt adera-frontend/package.json adera-frontend/package-lock.json; do
    if [[ ! -f "$file" ]]; then
        echo "ERROR: Required file is missing: $file"
        exit 1
    fi
done

command -v python3 >/dev/null 2>&1 || {
    echo "ERROR: Install Python 3 first."
    exit 1
}
command -v node >/dev/null 2>&1 || {
    echo "ERROR: Install Node.js first."
    exit 1
}
command -v npm >/dev/null 2>&1 || {
    echo "ERROR: npm is required."
    exit 1
}

if [[ ! -f .env ]]; then
    cp .env.example .env
    chmod 600 .env
    echo "Created .env. Configure your local values before starting the backend."
else
    echo "Existing .env preserved."
fi

if [[ ! -d .venv ]]; then
    python3 -m venv .venv || {
        echo "ERROR: Virtual environment creation failed."
        echo "On Kali/Debian, check whether python3-venv is installed."
        exit 1
    }
else
    echo "Existing .venv preserved."
fi

if [[ ! -x .venv/bin/python ]]; then
    echo "ERROR: .venv exists but its Python executable is missing."
    echo "Inspect it manually; this script will not replace it."
    exit 1
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

npm --prefix adera-frontend ci

echo
echo "Setup completed: Python and frontend dependencies installed."
echo "No database was created, changed, or migrated."
echo "Next: configure .env and ensure your PostgreSQL database is ready."
echo "Backend entry point: backend.main:app (port 8000)."
echo "Frontend: cd adera-frontend && npm run dev"
echo "For the isolated SQLite demo, follow docs/local-demo.md instead."
