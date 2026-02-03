#!/bin/bash

# Docker entrypoint for IGA Backend
# Runs migrations and optionally seeds data before starting the server

set -e

echo "============================================"
echo "IGA Backend - Starting up..."
echo "============================================"

# Wait for PostgreSQL to be ready
echo "[1/4] Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Run database migrations (always)
echo "[2/4] Running database migrations..."
alembic upgrade head || {
    echo "ERROR: Migration failed!"
    exit 1
}

# Run seeders (controlled by RUN_SEEDERS env)
echo "[3/4] Running database seeders..."
if [ "${RUN_SEEDERS:-true}" = "true" ]; then
    python -m app.seeders.runner || {
        echo "Warning: Seeding had errors, continuing..."
    }
else
    echo "Seeding skipped (RUN_SEEDERS=false)"
fi

# Start the server
echo "[4/4] Starting Uvicorn server..."
echo "============================================"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000