FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl for docker compose healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install pinned dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Alembic configuration and backend code
COPY alembic.ini ./
COPY backend/ ./backend/

# Copy entrypoint script
COPY scripts/docker-backend-entrypoint.sh /usr/local/bin/docker-backend-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-backend-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/docker-backend-entrypoint.sh"]
