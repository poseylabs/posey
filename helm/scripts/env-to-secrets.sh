#!/bin/bash

# Script to convert .env files to Kubernetes secrets

if [ $# -lt 2 ]; then
  echo "Usage: $0 <env-file> <secret-name> [namespace]"
  echo "Example: $0 .env api-credentials default"
  exit 1
fi

ENV_FILE=$1
SECRET_NAME=$2
NAMESPACE=${3:-default}

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: Environment file $ENV_FILE does not exist."
  exit 1
fi

# Create a temporary file for the kubectl command
TMP_FILE=$(mktemp)

echo "Creating Kubernetes secret $SECRET_NAME from $ENV_FILE"
echo "apiVersion: v1" > $TMP_FILE
echo "kind: Secret" >> $TMP_FILE
echo "metadata:" >> $TMP_FILE
echo "  name: $SECRET_NAME" >> $TMP_FILE
echo "  namespace: $NAMESPACE" >> $TMP_FILE
echo "type: Opaque" >> $TMP_FILE
echo "data:" >> $TMP_FILE

# Read each line from the .env file and convert to base64
while IFS='=' read -r key value || [ -n "$key" ]; do
  # Skip empty lines and comments
  if [ -z "$key" ] || [[ $key == \#* ]]; then
    continue
  fi
  
  # Remove any quotes around the value
  value=$(echo $value | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
  
  # Convert value to base64 and add to the kubectl command
  encoded=$(echo -n "$value" | base64)
  echo "  $key: $encoded" >> $TMP_FILE
done < "$ENV_FILE"

echo "Secret YAML created at $TMP_FILE"
echo "To apply the secret to your cluster, run:"
echo "kubectl apply -f $TMP_FILE"
echo "To apply and then remove the temporary file, run:"
echo "kubectl apply -f $TMP_FILE && rm $TMP_FILE" 