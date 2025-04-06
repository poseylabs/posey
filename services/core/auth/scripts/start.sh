#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running start.sh..."

# Run migrations first
echo "Running database migrations..."
sh /app/services/core/auth/scripts/run-migrations.sh
echo "Migrations finished."

# Execute the main application process, replacing the shell process.
# This ensures signals (like SIGTERM from Kubernetes) are passed correctly.
echo "Starting Node application: yarn node ./dist/main.js"
exec yarn node /app/services/core/auth/dist/main.js

echo "start.sh finished (should not be reached if exec worked)" 