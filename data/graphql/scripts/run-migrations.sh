#!/bin/bash
set -e

export PATH="/usr/lib/postgresql/15/bin:${PATH}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

# Debug - print all environment variables
echo "DEBUG: Environment variables:"
env | sort

# Extract port number if POSTGRES_PORT contains a URL
if [[ "${POSTGRES_PORT}" == tcp://* ]]; then
    echo "Detected Kubernetes-style POSTGRES_PORT: ${POSTGRES_PORT}, extracting port number..."
    POSTGRES_PORT_NUMBER=$(echo "${POSTGRES_PORT}" | sed -E 's|^.*:([0-9]+)$|\1|')
    echo "Extracted port number: ${POSTGRES_PORT_NUMBER}"
else
    POSTGRES_PORT_NUMBER="${POSTGRES_PORT}"
fi

# Use POSTGRES_SERVICE_HOST if POSTGRES_HOST is not set
if [ -z "${POSTGRES_HOST}" ] && [ ! -z "${POSTGRES_SERVICE_HOST}" ]; then
    echo "POSTGRES_HOST not set, using POSTGRES_SERVICE_HOST: ${POSTGRES_SERVICE_HOST}"
    POSTGRES_HOST_VALUE="${POSTGRES_SERVICE_HOST}"
else
    POSTGRES_HOST_VALUE="${POSTGRES_HOST}"
fi

# Ensure we have a database name
if [ -z "${POSTGRES_DB_POSEY}" ]; then
    echo "POSTGRES_DB_POSEY not set, defaulting to 'posey'"
    POSTGRES_DB_POSEY="posey"
fi

echo "Connecting to PostgreSQL at ${POSTGRES_HOST_VALUE}:${POSTGRES_PORT_NUMBER}, database ${POSTGRES_DB_POSEY}..."

# Wait for PostgreSQL to be ready with increased retry
retry_count=0
max_retries=30
until pg_isready -h "${POSTGRES_HOST_VALUE}" -p "${POSTGRES_PORT_NUMBER}" -U "${POSTGRES_USER}" || [ $retry_count -eq $max_retries ]; do
    retry_count=$((retry_count+1))
    echo "Waiting for PostgreSQL to be ready... (attempt $retry_count of $max_retries)"
    sleep 5
done

if [ $retry_count -eq $max_retries ]; then
    echo "Failed to connect to PostgreSQL after $max_retries attempts. Continuing anyway..."
else
    echo "PostgreSQL is ready!"
fi

# Check if starting fresh or if Hasura schema already exists
echo "Checking if Hasura schema (hdb_catalog) exists..."
SCHEMA_EXISTS=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST_VALUE}" -p "${POSTGRES_PORT_NUMBER}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB_POSEY}" -t -c "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'hdb_catalog');")

if [[ $SCHEMA_EXISTS == *"t"* ]]; then
    echo "Hasura schema exists. Attempting to drop it to allow Hasura to create fresh tables..."
    
    # Use a direct SQL file to avoid shell escaping issues
    cat > /tmp/drop_schema.sql << EOF
DROP SCHEMA IF EXISTS hdb_catalog CASCADE;
EOF
    
    # Execute the SQL file
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST_VALUE}" -p "${POSTGRES_PORT_NUMBER}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB_POSEY}" -f /tmp/drop_schema.sql || {
        echo "Could not drop schema. This is not necessarily an error - Hasura may still be able to use the existing schema."
    }
    
    # Clean up temp file
    rm /tmp/drop_schema.sql
else
    echo "Hasura schema does not exist. This is a fresh installation."
fi

# Run any custom migrations
if [ -d "/app/src/migrations" ]; then
    echo "Migrations directory exists, checking for SQL files..."
    migration_count=$(find /app/src/migrations -name "*.sql" | wc -l)
    if [ "$migration_count" -gt 0 ]; then
        echo "Found $migration_count SQL migration files to run."
        for f in /app/src/migrations/*.sql; do
            if [ -f "$f" ]; then
                if [[ "$f" != *"001_hasura_init.sql"* ]]; then
                    echo "Running migration: $f"
                    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST_VALUE}" -p "${POSTGRES_PORT_NUMBER}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB_POSEY}" -f "$f" || echo "Migration $f failed but continuing..."
                else
                    echo "Skipping Hasura init migration: $f (letting Hasura create its own schema)"
                fi
            fi
        done
        echo "Migrations completed."
    else
        echo "No SQL files found in migrations directory."
    fi
else
    echo "No migrations directory found at /app/src/migrations"
fi

echo "Migration process finished."
