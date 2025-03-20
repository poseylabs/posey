#!/bin/bash
set -e

echo "Running PostgreSQL startup script..."

# Initialize Hasura metadata tables
echo "Initializing Hasura metadata tables"
psql -U "$POSTGRES_USER" -d posey -p "$POSTGRES_PORT" <<EOF
-- Create Hasura catalog schema if not exists
CREATE SCHEMA IF NOT EXISTS hdb_catalog;

-- Create basic Hasura metadata table
CREATE TABLE IF NOT EXISTS hdb_catalog.hdb_metadata (
    id INTEGER PRIMARY KEY,
    metadata JSONB NOT NULL,
    resource_version INTEGER NOT NULL DEFAULT 1
);

-- Insert default metadata if not exists
INSERT INTO hdb_catalog.hdb_metadata (id, metadata)
SELECT 1, '{}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM hdb_catalog.hdb_metadata WHERE id = 1);

-- Create basic Hasura cron events table
CREATE TABLE IF NOT EXISTS hdb_catalog.hdb_cron_events (
    id TEXT PRIMARY KEY,
    trigger_name TEXT NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',
    tries INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    next_retry_at TIMESTAMPTZ,
    payload JSONB
);

-- Create indexes for cron events
CREATE INDEX IF NOT EXISTS hdb_cron_events_scheduled_time_idx ON hdb_catalog.hdb_cron_events (scheduled_time) WHERE status = 'scheduled';
CREATE INDEX IF NOT EXISTS hdb_cron_events_status_idx ON hdb_catalog.hdb_cron_events (status);
EOF

echo "Hasura metadata tables initialized"

# Ensure PostgreSQL listens on all interfaces
echo "Configuring PostgreSQL to listen on all interfaces"

# If the configuration file exists, modify it
if [ -f "$PGDATA/postgresql.conf" ]; then
  # Backup the original file
  cp "$PGDATA/postgresql.conf" "$PGDATA/postgresql.conf.bak"
  
  # Update the configuration
  sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PGDATA/postgresql.conf"
  sed -i "s/#port = 5432/port = 3333/" "$PGDATA/postgresql.conf"
  
  # Allow all connections on port 3333
  echo "host all all 0.0.0.0/0 trust" >> "$PGDATA/pg_hba.conf"
  
  echo "PostgreSQL configuration updated"
else
  echo "PostgreSQL configuration file not found at $PGDATA/postgresql.conf"
fi

# Start PostgreSQL with modified configuration
echo "Starting PostgreSQL with specific configuration options"
exec postgres -c listen_addresses='*' -c port=3333 "$@"
