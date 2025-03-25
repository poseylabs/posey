#!/bin/bash
set -e

# Try multiple connection options
export PGHOST=localhost
export PGPORT=3333
echo "Trying to connect to PostgreSQL at $PGHOST:$PGPORT"

# Wait for PostgreSQL to be ready (Try both TCP and socket connections)
MAX_ATTEMPTS=30
ATTEMPT=1
CONNECTED=false

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
  echo "Connection attempt $ATTEMPT of $MAX_ATTEMPTS..."
  
  # Try TCP connection
  if pg_isready -h localhost -p 3333; then
    CONNECTED=true
    echo "Connected to PostgreSQL via TCP at localhost:3333"
    break
  fi
  
  # Try socket connection
  if pg_isready -U "$POSTGRES_USER"; then
    CONNECTED=true
    echo "Connected to PostgreSQL via socket"
    export PGHOST=/var/run/postgresql
    break
  fi
  
  sleep 2
  ATTEMPT=$((ATTEMPT+1))
done

if [ "$CONNECTED" = false ]; then
  echo "Could not connect to PostgreSQL after $MAX_ATTEMPTS attempts. Exiting."
  exit 1
fi

# Run all SQL files in migrations directory in order
if [ -d "/docker-entrypoint-initdb.d/migrations" ]; then
  for f in /docker-entrypoint-initdb.d/migrations/*.sql; do
    if [ -f "$f" ]; then
      echo "Running migration $f"
      psql -U "$POSTGRES_USER" -d "$POSTGRES_DB_POSEY" -c "\i $f"
    fi
  done
fi

# Initialize other application databases if needed
echo "Running migrations for inventory database"
if [ -d "/docker-entrypoint-initdb.d/app-migrations/inventory" ]; then
  for f in /docker-entrypoint-initdb.d/app-migrations/inventory/*.sql; do
    if [ -f "$f" ]; then
      echo "Running inventory migration $f"
      psql -U "$POSTGRES_USER" -d inventory -c "\i $f"
    fi
  done
fi

echo "Migrations completed successfully!"
