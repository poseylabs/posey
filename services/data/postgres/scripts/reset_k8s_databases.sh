#!/bin/bash
set -e

NAMESPACE="${NAMESPACE:-posey}"
POD_NAME="postgres-0"

echo "Resetting PostgreSQL databases in Kubernetes pod $POD_NAME in namespace $NAMESPACE..."

# Copy the reset script to the pod
kubectl cp scripts/reset_databases.sh $NAMESPACE/$POD_NAME:/tmp/reset_databases.sh

# Make it executable
kubectl exec -n $NAMESPACE $POD_NAME -- chmod +x /tmp/reset_databases.sh

# Set environment variable and run the script
kubectl exec -n $NAMESPACE $POD_NAME -- bash -c "export ENVIRONMENT=development && export POSTGRES_USER=pocketdb && /tmp/reset_databases.sh"

# Check if it was successful
if [ $? -eq 0 ]; then
  echo "Database reset completed successfully!"
else
  echo "Error: Database reset failed!"
  exit 1
fi

# Delete the temporary file
kubectl exec -n $NAMESPACE $POD_NAME -- rm /tmp/reset_databases.sh

echo "All done! Databases have been reset." 