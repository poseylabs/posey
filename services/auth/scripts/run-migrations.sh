#!/bin/bash
set -e

export PATH="/usr/lib/postgresql/15/bin:${PATH}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

DB_SCRIPTS_DIR="/app/services/auth/src/migrations/000_create_databases.sql"

# Wait for PostgreSQL to be ready
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}"; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done

echo "PostgreSQL is ready!"

# Create databases first (connect to default postgres database)
if [ -f DB_SCRIPTS_DIR ]; then
    echo "Creating databases if they don't exist..."
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "postgres" -f ${DB_SCRIPTS_DIR}
fi

# Run other migrations if they exist
if [ -d "/app/services/auth/src/migrations" ]; then
    for f in /app/services/auth/src/migrations/[0-9]*.sql; do
        if [ -f "$f" ] && [ "$f" != DB_SCRIPTS_DIR ]; then
            echo "Running migration: $f"
            PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB_SUPERTOKENS}" -f "$f"
        fi
    done
fi

echo "Migrations completed successfully"
