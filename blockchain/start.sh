#!/bin/sh
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Starting blockchain node..."
exec uvicorn node.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-5000}"
