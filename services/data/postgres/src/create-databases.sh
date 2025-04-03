#!/bin/bash
set -e

# Read databases from configuration file
DATABASES=$(jq -r '.databases[]' /docker-entrypoint-initdb.d/databases.json)

# Connect to default postgres database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
-- Connect to default postgres database first
\c postgres;

-- Terminate existing connections to databases we want to drop
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname <> 'postgres' 
AND pid <> pg_backend_pid();
EOSQL

# Drop and create each database
for db in $DATABASES; do
  echo "Creating database: $db"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DROP DATABASE IF EXISTS $db;
    CREATE DATABASE $db;
EOSQL
done

echo "All application databases have been created" 