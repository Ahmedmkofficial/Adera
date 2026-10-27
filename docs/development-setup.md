# Adera Development Setup

This guide walks you through setting up and running Adera locally on Linux, macOS, and Windows.

---

## 1. Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.10+**: `python3 --version` (or `python --version` on Windows)
- **Node.js (v18+) and npm**: `node -v` and `npm -v`
- **Git**: `git --version`
- **Docker & Docker Compose** *(recommended for running PostgreSQL without manual setup)*: `docker compose version`

---

## 2. Automated Dependency Installation

Adera includes automated setup scripts that configure the local environment, create a root virtual environment (`.venv`), install Python packages, and install frontend dependencies via `npm ci`.

### Linux / macOS

```bash
bash scripts/setup.sh
```

### Windows (PowerShell)

Open PowerShell as your normal user and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

### What the setup script performs:
1. Validates repository files (`.env.example`, `requirements.txt`, `adera-frontend/package.json`, etc.).
2. Checks that Python, Node.js, and npm are available in `PATH`.
3. Safely creates `.env` from `.env.example` if it does not already exist (preserves any existing `.env`).
4. Creates a root Python virtual environment at `.venv/`.
5. Upgrades `pip` and installs all dependencies from `requirements.txt` (cross-platform with platform markers).
6. Runs `npm ci` inside `adera-frontend/` to install locked frontend packages.
7. Leaves database creation and migrations for the next step.

---

## 3. Database Options

You have two choices for your database:

### Option A: PostgreSQL via Docker Compose (Recommended)

To avoid installing and configuring PostgreSQL manually on your host system, use the database-only Docker Compose service:

1. **Start the database container:**
   ```bash
   docker compose up -d db
   ```
   This spins up an isolated PostgreSQL 16 service on port `5432` with a persistent named volume and predefined credentials matching `.env.example`.

   > **Note: If port 5432 is already occupied by a native PostgreSQL server:**
   >
   > Start the Compose database on an alternative host port such as `5433`:
   > - **Linux / macOS:**
   >   ```bash
   >   POSTGRES_PORT=5433 docker compose up -d db
   >   ```
   > - **Windows (PowerShell):**
   >   ```powershell
   >   $env:POSTGRES_PORT = "5433"; docker compose up -d db
   >   ```
   > *Important:* `POSTGRES_PORT` controls the Docker host-port mapping; it does not automatically rewrite `DATABASE_URL`. When using port `5433`, update `DATABASE_URL` in your `.env` (e.g. `postgresql://<user>:<password>@localhost:5433/adera_db`, using credentials from your own local configuration) so the backend and Alembic connect to this container.

2. **Wait for the database health check to pass:**
   ```bash
   docker compose ps
   ```
   Verify that `adera-postgres` status displays `healthy`.

3. **Verify or customize `.env`:**
   Check that `.env` contains the matching `DATABASE_URL` and a valid secret key:
   ```text
   DATABASE_URL=postgresql://adera_user:your_password@localhost:5432/adera_db
   JWT_SECRET_KEY=replace-with-a-random-secret-of-at-least-32-bytes
   ```

4. **Apply Alembic migrations:**
   - Linux / macOS:
     ```bash
     .venv/bin/alembic upgrade head
     ```
   - Windows (PowerShell):
     ```powershell
     .\.venv\Scripts\alembic.exe upgrade head
     ```

### Option B: Isolated Local SQLite Demo (Zero PostgreSQL)

If you want to immediately explore the UI and test features without using PostgreSQL or Docker:
- Follow the instructions in [docs/local-demo.md](local-demo.md).
- This creates a sandboxed SQLite database in `.local-demo/` with synthetic accounts, reports, and analyst credentials.

---

## 4. Running the Application

### Terminal 1: Backend API (FastAPI)

From the repository root:

- **Linux / macOS:**
  ```bash
  .venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
  ```
- **Windows (PowerShell):**
  ```powershell
  .\.venv\Scripts\uvicorn.exe backend.main:app --reload --host 127.0.0.1 --port 8000
  ```

API documentation will be accessible at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Terminal 2: Frontend (React / Vite)

From the repository root:

```bash
cd adera-frontend
npm run dev
```

Open the printed Vite URL in your browser (typically `http://localhost:5173` or `http://127.0.0.1:5173`). Vite proxies API requests to `http://127.0.0.1:8000/api`.

---

## 5. Running Tests

### Backend Tests

Run automated tests against an isolated in-memory SQLite database:

- **Linux / macOS:**
  ```bash
  DATABASE_URL=sqlite:// .venv/bin/pytest
  ```
- **Windows (PowerShell):**
  ```powershell
  $env:DATABASE_URL="sqlite://"; .\.venv\Scripts\pytest.exe; Remove-Item Env:\DATABASE_URL
  ```

### Frontend Tests & Checks

From the `adera-frontend/` directory:

```bash
cd adera-frontend
npm run lint
npm test
npm run build
```
