#!/bin/bash

# Docker entrypoint for IGA Backend

# Runs migrations and seeds data before starting the server



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



# Run database migrations

echo "[2/4] Running database migrations..."

alembic upgrade head



# Seed sample data (only if needed)

echo "[3/4] Checking/seeding sample data..."

python -c "from app.seed_data import seed_multitenancy_data; seed_multitenancy_data()" || true



# Start the server

echo "[4/4] Starting Uvicorn server..."

echo "============================================"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000