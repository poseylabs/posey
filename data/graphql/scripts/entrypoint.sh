#!/bin/sh
set -e

echo "Starting custom entrypoint script..."

# First run our migration script to drop existing Hasura schema
echo "Running migration script to clean up environment..."
/app/scripts/run-migrations.sh

# Now start Hasura
echo "Starting Hasura GraphQL Engine..."

# Start Hasura GraphQL Engine
exec graphql-engine serve 