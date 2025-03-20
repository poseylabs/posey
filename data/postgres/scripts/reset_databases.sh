#!/bin/bash
set -e

if [ "$ENVIRONMENT" != "development" ] && [ "$ENVIRONMENT" != "local" ]; then
  echo "This script only runs in development/local environments."
  echo "Current environment: $ENVIRONMENT"
  exit 0
fi

echo "Resetting all user databases in PostgreSQL..."

# Get a list of databases to drop
DATABASES_TO_DROP=$(psql -U "$POSTGRES_USER" -d postgres -t -c "SELECT datname FROM pg_database WHERE datname NOT IN ('postgres', 'template0', 'template1') AND datistemplate = false;")

# Terminate connections and drop each database
for DB in $DATABASES_TO_DROP; do
  echo "Terminating connections and dropping database: $DB"
  psql -U "$POSTGRES_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB' AND pid <> pg_backend_pid();"
  psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB;"
done

echo "All user databases have been dropped successfully."

# Ensure the posey database is created
psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE posey OWNER $POSTGRES_USER;"
echo "Created posey database owned by $POSTGRES_USER"

# Create extensions if needed
psql -U "$POSTGRES_USER" -d posey -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"; CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";"
echo "Extensions created in posey database"

echo "Database reset completed successfully." 