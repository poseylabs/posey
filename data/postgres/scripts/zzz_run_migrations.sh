#!/bin/bash
set -e

echo "Running migrations with Unix socket connection..."

# Create posey database if it doesn't exist
echo "Checking if posey database exists..."
psql -U "$POSTGRES_USER" -d postgres -c "SELECT 1 FROM pg_database WHERE datname = 'posey'" | grep -q 1 || \
psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE posey OWNER $POSTGRES_USER;"

# Initialize Hasura metadata tables
if [ -f "/docker-entrypoint-initdb.d/hasura-init.sql" ]; then
  echo "Initializing Hasura metadata tables"
  psql -U "$POSTGRES_USER" -d postgres -c "\i /docker-entrypoint-initdb.d/hasura-init.sql"
else
  echo "Hasura initialization file not found, skipping"
fi

# Run all SQL files in migrations directory in order
if [ -d "/docker-entrypoint-initdb.d/migrations" ]; then
  echo "Running migrations from /docker-entrypoint-initdb.d/migrations/"
  for f in /docker-entrypoint-initdb.d/migrations/*.sql; do
    if [ -f "$f" ]; then
      echo "Running migration $f"
      psql -U "$POSTGRES_USER" -d "posey" -c "\i $f"
    fi
  done
else
  echo "No migrations directory found, skipping migrations"
fi

# Create extensions
echo "Creating extensions in posey database"
psql -U "$POSTGRES_USER" -d "posey" -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"; CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";"

# Initialize other application databases if needed
echo "All migrations completed successfully!" 