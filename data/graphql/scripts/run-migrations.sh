#!/bin/bash
set -e

export PATH="/usr/lib/postgresql/15/bin:${PATH}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

# Wait for PostgreSQL to be ready
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}"; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done

echo "PostgreSQL is ready!"

# Run migrations if they exist
if [ -d "/app/src/migrations" ]; then
    for f in /app/src/migrations/*.sql; do
        if [ -f "$f" ]; then
            echo "Running migration: $f"
            PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB_POSEY}" -f "$f"
        fi
    done
fi

echo "Migrations completed successfully"
