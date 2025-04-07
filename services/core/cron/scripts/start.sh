#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running start.sh for cron service..."

# Add any cron-specific pre-start logic here if needed in the future

# Execute the main application process using yarn node
echo "Starting Node application: yarn node ./dist/index.js"
exec yarn node /app/services/core/cron/dist/index.js

echo "start.sh finished (should not be reached if exec worked)" 