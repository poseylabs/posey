#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB_POSEY" -p "$POSTGRES_PORT"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Run all SQL files in migrations directory in order
for f in /docker-entrypoint-initdb.d/migrations/*.sql; do
  echo "Running migration $f"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB_POSEY" -p "$POSTGRES_PORT" -f "$f"
done

echo "Migrations completed"
