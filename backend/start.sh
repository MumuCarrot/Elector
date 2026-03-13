#!/bin/sh
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Starting FastAPI server..."
exec python -m backend.app.main