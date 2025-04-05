#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running start.sh..."

# Execute the main application process, replacing the shell process.
# This ensures signals (like SIGTERM from Kubernetes) are passed correctly.
echo "Starting Node application: node ./dist/main.js"
exec node ./dist/main.js

echo "start.sh finished (should not be reached if exec worked)" 