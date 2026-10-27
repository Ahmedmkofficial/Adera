$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "=== Adera setup: Windows ==="

# Validate repository files before installing anything.
$requiredFiles = @(
    ".env.example",
    "requirements.txt",
    "adera-frontend/package.json",
    "adera-frontend/package-lock.json"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file -PathType Leaf)) {
        throw "Required file is missing: $file"
    }
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3 is required. Install it and reopen PowerShell."
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is required. Install it and reopen PowerShell."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm is required. Install Node.js and reopen PowerShell."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env. Configure your local values before starting the backend."
} else {
    Write-Host "Existing .env preserved."
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
} else {
    Write-Host "Existing .venv preserved."
}

$pythonExe = Join-Path (Get-Location) ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe -PathType Leaf)) {
    throw ".venv exists but its Python executable is missing. Inspect it manually; it will not be replaced."
}

& $pythonExe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip."
}

& $pythonExe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install Python dependencies."
}

Push-Location "adera-frontend"
try {
    npm ci
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install frontend dependencies."
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Setup completed: Python and frontend dependencies installed."
Write-Host "No database was created, changed, or migrated."
Write-Host "Next: configure .env and ensure your PostgreSQL database is ready."
Write-Host "Backend entry point: backend.main:app (port 8000)."
Write-Host "Frontend: cd adera-frontend; npm run dev"
Write-Host "For the isolated SQLite demo, follow docs/local-demo.md instead."
