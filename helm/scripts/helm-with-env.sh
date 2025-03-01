#!/bin/bash

# Enhanced script to install/upgrade Helm chart with secrets from multiple .env files
# Designed for monorepo structures with multiple services and applications

set -e

# Default values
ACTION="install"
RELEASE_NAME="posey"
CHART_PATH="./helm/posey"
NAMESPACE="default"
VALUES_FILE="./helm/posey/values.yaml"
TMP_SECRET_FILE=$(mktemp)

# Default .env files - add all .env files that should be loaded by default
ENV_FILES=(
  "./services/.env"
  "./data/.env"
  "./apps/www/.env"
)

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --action)
      ACTION="$2"
      shift 2
      ;;
    --env-files)
      IFS=',' read -ra ENV_FILES <<< "$2"
      shift 2
      ;;
    --release)
      RELEASE_NAME="$2"
      shift 2
      ;;
    --chart)
      CHART_PATH="$2"
      shift 2
      ;;
    --namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    --values)
      VALUES_FILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate action
if [[ "$ACTION" != "install" && "$ACTION" != "upgrade" && "$ACTION" != "uninstall" ]]; then
  echo "Error: Invalid action. Use 'install', 'upgrade', or 'uninstall'."
  exit 1
fi

# For uninstall, just run the command and exit
if [[ "$ACTION" == "uninstall" ]]; then
  echo "Uninstalling Helm release $RELEASE_NAME..."
  helm uninstall "$RELEASE_NAME"
  exit 0
fi

# Create a temporary values file for secrets
echo "# Auto-generated secrets file" > "$TMP_SECRET_FILE"
echo "apikeys:" >> "$TMP_SECRET_FILE"
echo "environment:" >> "$TMP_SECRET_FILE"
echo "  nodeEnv: development" >> "$TMP_SECRET_FILE"
echo "services:" >> "$TMP_SECRET_FILE"
echo "  postgres:" >> "$TMP_SECRET_FILE"
echo "    host: posey-postgres" >> "$TMP_SECRET_FILE"
echo "    port: \"3333\"" >> "$TMP_SECRET_FILE"
echo "    user: \"pocketdb\"" >> "$TMP_SECRET_FILE"
echo "databases:" >> "$TMP_SECRET_FILE"
echo "  postgres:" >> "$TMP_SECRET_FILE"
echo "    password: \"placeholder\"" >> "$TMP_SECRET_FILE"
echo "secrets:" >> "$TMP_SECRET_FILE"
echo "  jwt:" >> "$TMP_SECRET_FILE"
echo "  digitalOcean:" >> "$TMP_SECRET_FILE"
echo "  ai:" >> "$TMP_SECRET_FILE"
echo "  google:" >> "$TMP_SECRET_FILE"
echo "  flux:" >> "$TMP_SECRET_FILE"
echo "  superTokens:" >> "$TMP_SECRET_FILE"
echo "  npm:" >> "$TMP_SECRET_FILE"
echo "  dashboard:" >> "$TMP_SECRET_FILE"

# Process each .env file
for ENV_FILE in "${ENV_FILES[@]}"; do
  if [[ -f "$ENV_FILE" ]]; then
    echo "Processing $ENV_FILE..."
    
    # Extract values from the .env file
    while IFS='=' read -r key value || [ -n "$key" ]; do
      # Skip empty lines and comments
      if [ -z "$key" ] || [[ $key == \#* ]]; then
        continue
      fi
      
      # Remove quotes and trailing/leading whitespace
      value=$(echo "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
      
      # Map environment variables to Helm values structure
      case "$key" in
        # Environment settings
        NODE_ENV)
          echo "environment:" >> "$TMP_SECRET_FILE"
          echo "  nodeEnv: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        
        # Database settings
        POSTGRES_USER)
          echo "services:" >> "$TMP_SECRET_FILE"
          echo "  postgres:" >> "$TMP_SECRET_FILE"
          echo "    user: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        POSTGRES_PORT)
          echo "services:" >> "$TMP_SECRET_FILE"
          echo "  postgres:" >> "$TMP_SECRET_FILE"
          echo "    port: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        POSTGRES_HOST)
          echo "services:" >> "$TMP_SECRET_FILE"
          echo "  postgres:" >> "$TMP_SECRET_FILE"
          echo "    host: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        POSTGRES_PASSWORD)
          echo "databases:" >> "$TMP_SECRET_FILE"
          echo "  postgres:" >> "$TMP_SECRET_FILE"
          echo "    password: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        POSTGRES_DB_POSEY)
          echo "databases:" >> "$TMP_SECRET_FILE"
          echo "  postgres:" >> "$TMP_SECRET_FILE"
          echo "    dbPosey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
          
        # API Keys
        ANTHROPIC_API_KEY)
          echo "apikeys:" >> "$TMP_SECRET_FILE"
          echo "  anthropic: \"$value\"" >> "$TMP_SECRET_FILE"
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  ai:" >> "$TMP_SECRET_FILE"
          echo "    anthropicApiKey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        OPENAI_API_KEY)
          echo "apikeys:" >> "$TMP_SECRET_FILE"
          echo "  openai: \"$value\"" >> "$TMP_SECRET_FILE"
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  ai:" >> "$TMP_SECRET_FILE"
          echo "    openaiApiKey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        GEMINI_API_KEY)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  ai:" >> "$TMP_SECRET_FILE"
          echo "    geminiApiKey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        STABLE_DIFFUSION_API_KEY)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  ai:" >> "$TMP_SECRET_FILE"
          echo "    stableDiffusionApiKey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        STABLE_DIFFUSION_TOKEN)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  ai:" >> "$TMP_SECRET_FILE"
          echo "    stableDiffusionToken: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        
        # JWT & Auth
        JWT_SECRET_KEY)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  jwt:" >> "$TMP_SECRET_FILE"
          echo "    secretKey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        SUPERTOKENS_API_KEY)
          echo "apikeys:" >> "$TMP_SECRET_FILE"
          echo "  supertokens: \"$value\"" >> "$TMP_SECRET_FILE"
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  superTokens:" >> "$TMP_SECRET_FILE"
          echo "    apiKey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        
        # Digital Ocean
        DIGITALOCEAN_ACCESS_TOKEN)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  digitalOcean:" >> "$TMP_SECRET_FILE"
          echo "    accessToken: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        DO_STORAGE_BUCKET_KEY)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  digitalOcean:" >> "$TMP_SECRET_FILE"
          echo "    storageBucketKey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        DO_STORAGE_BUCKET_SECRET)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  digitalOcean:" >> "$TMP_SECRET_FILE"
          echo "    storageBucketSecret: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        
        # Google
        GOOGLE_CLIENT_ID)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  google:" >> "$TMP_SECRET_FILE"
          echo "    clientId: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        GOOGLE_CLIENT_SECRET)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  google:" >> "$TMP_SECRET_FILE"
          echo "    clientSecret: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        
        # Flux
        FLUX_API_KEY)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  flux:" >> "$TMP_SECRET_FILE"
          echo "    apiKey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
        
        # Dashboard
        DASHBOARD_API_KEY)
          echo "secrets:" >> "$TMP_SECRET_FILE"
          echo "  dashboard:" >> "$TMP_SECRET_FILE"
          echo "    apiKey: \"$value\"" >> "$TMP_SECRET_FILE"
          ;;
      esac
    done < "$ENV_FILE"
  else
    echo "Warning: Environment file $ENV_FILE does not exist, skipping..."
  fi
done

# Debug: Show what's being loaded (but hide values)
echo "Generated secrets from the following files:"
for ENV_FILE in "${ENV_FILES[@]}"; do
  if [[ -f "$ENV_FILE" ]]; then
    echo " - $ENV_FILE"
  fi
done

# Create Docker registry secret for DigitalOcean if DIGITALOCEAN_ACCESS_TOKEN exists
DO_TOKEN=$(grep DIGITALOCEAN_ACCESS_TOKEN .env | cut -d= -f2 | tr -d '"' | tr -d "'")
if [ ! -z "$DO_TOKEN" ]; then
  echo "Creating Docker registry secret for DigitalOcean..."
  kubectl delete secret registry-digitalocean --ignore-not-found
  kubectl create secret docker-registry registry-digitalocean \
    --docker-server=registry.digitalocean.com \
    --docker-username=do-access-token \
    --docker-password="$DO_TOKEN" \
    --namespace "$NAMESPACE"
  
  # Patch default service account to use this secret
  kubectl patch serviceaccount default -p '{"imagePullSecrets":[{"name":"registry-digitalocean"}]}' --namespace "$NAMESPACE"
fi

# Run Helm command
if [[ "$ACTION" == "install" ]]; then
  echo "Installing Helm chart $CHART_PATH as $RELEASE_NAME..."
  helm install "$RELEASE_NAME" "$CHART_PATH" -f "$VALUES_FILE" -f "$TMP_SECRET_FILE" --namespace "$NAMESPACE"
elif [[ "$ACTION" == "upgrade" ]]; then
  echo "Upgrading Helm release $RELEASE_NAME..."
  helm upgrade "$RELEASE_NAME" "$CHART_PATH" -f "$VALUES_FILE" -f "$TMP_SECRET_FILE" --namespace "$NAMESPACE"
fi

# Clean up
echo "Cleaning up temporary files..."
rm "$TMP_SECRET_FILE"

echo "Deployment completed successfully!" 