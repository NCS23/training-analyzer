#!/bin/sh

echo "Waiting for PostgreSQL..."
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:]*\):\([0-9]*\)/.*|\1|p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:]*\):\([0-9]*\)/.*|\2|p')

for i in $(seq 1 30); do
  if pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; then
    echo "PostgreSQL is ready."
    break
  fi
  echo "Waiting for PostgreSQL ($i/30)..."
  sleep 2
done

echo "Current Alembic version:"
alembic current 2>&1 || echo "Could not determine Alembic version."

echo "Running Alembic migrations..."
if alembic upgrade head; then
  echo "Migrations completed successfully."
else
  echo "WARNING: Alembic migrations failed (exit code $?). Starting app anyway."
fi

echo "Alembic version after migration:"
alembic current 2>&1 || echo "Could not determine Alembic version."

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
