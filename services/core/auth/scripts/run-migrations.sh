#!/bin/bash
set -e

export PATH="/usr/lib/postgresql/15/bin:${PATH}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

# Print connection variables for debugging
echo "--- PostgreSQL Connection Info (run-migrations.sh) ---"
echo "POSTGRES_HOST: ${POSTGRES_HOST}"
echo "POSTGRES_PORT: ${POSTGRES_PORT}"
echo "POSTGRES_USER: ${POSTGRES_USER}"
# Avoid printing password: echo "POSTGRES_PASSWORD: [set]"
echo "-----------------------------------------------------"

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
            echo "Running migration: $f on database ${POSTGRES_DB_SUPERTOKENS}"
            # Use the supertokens database for auth-specific migrations
            PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB_SUPERTOKENS}" -f "$f"
        fi
    done
fi

echo "Migrations completed successfully"
