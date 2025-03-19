#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB_POSEY" -p "$POSTGRES_PORT"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Initialize Hasura metadata tables
echo "Initializing Hasura metadata tables"
psql -U "$POSTGRES_USER" -d postgres -p "$POSTGRES_PORT" -f /docker-entrypoint-initdb.d/hasura-init.sql

# Run all SQL files in migrations directory in order
for f in /docker-entrypoint-initdb.d/migrations/*.sql; do
  echo "Running migration $f"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB_POSEY" -p "$POSTGRES_PORT" -f "$f"
done

# Initialize other application databases if needed
echo "Running migrations for inventory database"
if [ -d "/docker-entrypoint-initdb.d/app-migrations/inventory" ]; then
  for f in /docker-entrypoint-initdb.d/app-migrations/inventory/*.sql; do
    echo "Running inventory migration $f"
    psql -U "$POSTGRES_USER" -d inventory -p "$POSTGRES_PORT" -f "$f"
  done
fi

echo "Migrations completed"
