# Adera Development Setup

This guide walks you through setting up and running Adera locally on Linux, macOS, and Windows.

---

## 1. Prerequisites

Ensure you have the following installed on your machine:
- **Docker & Docker Compose**: `docker compose version` (Compose v2 recommended)
- **Node.js (v18+) and npm** *(for local development/testing)*: `node -v` and `npm -v`
- **Python 3.10+** *(for local development/testing)*: `python3 --version`
- **Git**: `git --version`

---

## 2. Docker Compose (Full Environment: PostgreSQL, Backend, Frontend)

Docker Compose orchestrates all three services with a single command:
- **`db`**: PostgreSQL 16 (on container port 5432, host port mapped to `5433` by default).
- **`backend`**: FastAPI application with healthchecks. Pending database migrations are applied on startup (port 8000).
- **`frontend`**: React / Vite application configured with reverse-proxying to the backend (port 5173).

### Step 1: Environment Configuration
Copy `.env.example` to `.env` if not already present:
```bash
cp .env.example .env
```
Generate a secure 32-byte JWT secret key and set it in `.env`:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# or
openssl rand -hex 32
```

> **Host Port 5432 & Native PostgreSQL:**
> Systems such as Kali Linux often run native PostgreSQL on port 5432. The Docker Compose configuration defaults `POSTGRES_PORT` to `5433` so host native databases and containers never conflict. Within the Docker network, containers communicate over internal port `5432` (`db:5432`).

### Step 2: First Startup
Build the container images and start all three services in detached mode:
```bash
docker compose up --build -d
```

### Step 3: Check Status & Health
Verify that all services are up and healthy:
```bash
docker compose ps
```
You should see:
- `adera-postgres`: Up (healthy)
- `adera-backend`: Up (healthy)
- `adera-frontend`: Up (healthy)

### Step 4: Access the Application
- **Frontend Web UI**: [http://localhost:5173](http://localhost:5173)
  - Preconfigured with `VITE_USE_MOCK=false`.
  - Vite dev server reverse-proxies API requests (`/auth`, `/risk`, `/reports`, `/cases`, etc.) to the backend container.
- **Backend API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Step 5: View Logs
Follow logs for all services or an individual service:
```bash
# All services
docker compose logs -f

# Individual service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### Step 6: Stopping Services & Preserving Data
To stop the running services:
```bash
docker compose down
```

> [!CAUTION]
> **Preserving Database Data:**
> Never run `docker compose down -v` or delete Docker volumes. The PostgreSQL data is stored in the persistent named volume `adera_adera_pgdata`. Running `docker compose down` safely stops containers while preserving the volume and all stored data.

### Subsequent Starts
To start services again without rebuilding:
```bash
docker compose up -d
```

---

## 3. Database Migrations

Database migrations are managed via Alembic (`backend/alembic/`).
- When the backend container starts, pending migrations are applied automatically via `alembic upgrade head` before launching Uvicorn.
- Alembic checks the `alembic_version` table. If the database is already up-to-date, this is an immediate no-op. Because schema migrations alter tables, pending migration scripts should always be reviewed carefully before production deployment.
- To inspect migration status manually:
  ```bash
  # Inside the backend container:
  docker compose exec backend alembic current
  docker compose exec backend alembic heads

  # Or from host Python virtual environment (port 5433):
  DATABASE_URL="postgresql://adera_user:your_password@localhost:5433/adera_db" .venv/bin/alembic current
  ```

---

## 4. Host-Based Local Development (Hybrid Workflow)

If you prefer running the backend or frontend directly on your host machine while using PostgreSQL in Docker:

1. **Start only the database service:**
   ```bash
   docker compose up -d db
   ```
2. **Setup host Python environment & frontend dependencies:**
   ```bash
   bash scripts/setup.sh
   ```
3. **Run backend locally:**
   ```bash
   DATABASE_URL="postgresql://adera_user:your_password@localhost:5433/adera_db" .venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
4. **Run frontend locally:**
   ```bash
   cd adera-frontend
   BACKEND_URL="http://127.0.0.1:8000" npm run dev
   ```

> [!IMPORTANT]
> **Local Demo Credentials:**
> The default administrator account (`username: admin`, `password: admin`) is intended strictly for local development and demonstration. Never use or seed these credentials in production environments.

---

## 5. Running Automated Tests

Always run tests against isolated in-memory or temporary databases to protect persistent development data:

### Backend Tests
```bash
DATABASE_URL=sqlite:// .venv/bin/pytest -q
```

### Frontend Tests & Quality Checks
```bash
cd adera-frontend
npm run lint
npm test
npm run build
```

---

## 6. Troubleshooting

- **Port 5432 conflict on host:** The Compose configuration defaults `POSTGRES_PORT` to `5433`. If you need another port, set `POSTGRES_PORT=5434` in your `.env`.
- **Backend cannot connect to database:** Check that `db` is healthy using `docker compose ps`. Containers connect via `db:5432`.
- **Frontend API requests fail:** Confirm `adera-backend` is healthy at `http://localhost:8000/health`. Vite proxies requests directly to `http://backend:8000`.
- **Container rebuild after dependency changes:** If you modify `requirements.txt` or `package.json`, rebuild the images using `docker compose up --build -d`.
