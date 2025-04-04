#!/bin/bash

# CircleCI env variable sync script
# This script syncs your local .env files to CircleCI using multiple contexts based on .env file sources

# Configuration
CIRCLECI_ORG_ID="4429f510-386b-4120-8059-6ba7c5f694e2"
PREFIX="posey-prod"

# Files to process with priority order (higher priority files will override earlier ones)
FILES=(".env" "services/data/.env" "services/.env" "apps/www/.env")

# Context names corresponding to each file (same order as FILES)
CONTEXTS=("$PREFIX-core" "$PREFIX-data" "$PREFIX-services" "$PREFIX-apps-www")

# Check if CircleCI CLI is installed
if ! command -v circleci &> /dev/null; then
  echo "CircleCI CLI not found. Installing..."
  curl -fLSs https://raw.githubusercontent.com/CircleCI-Public/circleci-cli/master/install.sh | bash
fi

# Check authentication
if ! circleci diagnostic | grep -q "token"; then
  echo "Please authenticate CircleCI CLI first"
  circleci setup
fi

# Exclusion list - variables to skip (add any variables you want to exclude)
EXCLUDE=(
  "TURBO_TEAM" "TURBO_TOKEN" "TURBO_REMOTE_CACHE_PROVIDER" "TURBO_REMOTE_CACHE_ENDPOINT"
  "TURBO_REMOTE_CACHE_REGION" "TURBO_REMOTE_CACHE_BUCKET"
  "NODE_ENV" "DEBUG" "ENVIRONMENT" "NODE_DEBUG"
  "WATCHPACK_POLLING"
)

# Function to check if a variable should be excluded
should_exclude() {
  local var="$1"
  for excluded in "${EXCLUDE[@]}"; do
    if [[ "$var" == "$excluded" ]]; then
      return 0
    fi
  done
  return 1
}

# Create a temporary directory to store our variables
TEMP_DIR=$(mktemp -d)
if [[ ! "$TEMP_DIR" || ! -d "$TEMP_DIR" ]]; then
  echo "Failed to create temp directory"
  exit 1
fi

# Create directories for each context
for context in "${CONTEXTS[@]}"; do
  mkdir -p "$TEMP_DIR/$context"
done

# Process each file
echo "Loading environment variables..."
TOTAL_VAR_COUNT=0

# Initialize context counts
CONTEXT_COUNTS=()
for i in "${!CONTEXTS[@]}"; do
  CONTEXT_COUNTS[$i]=0
done

for i in "${!FILES[@]}"; do
  file="${FILES[$i]}"
  context="${CONTEXTS[$i]}"
  
  if [ -f "$file" ]; then
    echo "Processing $file -> $context context..."
    
    while IFS= read -r line; do
      # Skip empty lines or comments
      if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
      fi
      
      # Extract variable name and value
      if [[ "$line" =~ ^([A-Za-z0-9_]+)=(.*) ]]; then
        VAR_NAME="${BASH_REMATCH[1]}"
        VAR_VALUE="${BASH_REMATCH[2]}"
        
        # Skip excluded variables
        if should_exclude "$VAR_NAME"; then
          echo "Skipping $VAR_NAME (excluded)"
          continue
        fi
        
        # Remove quotes if present
        if [[ $VAR_VALUE == \"*\" ]]; then
          VAR_VALUE="${VAR_VALUE#\"}"
          VAR_VALUE="${VAR_VALUE%\"}"
        elif [[ $VAR_VALUE == \'*\' ]]; then
          VAR_VALUE="${VAR_VALUE#\'}"
          VAR_VALUE="${VAR_VALUE%\'}"
        fi
        
        # Store each variable in appropriate context directory
        echo -n "$VAR_VALUE" > "$TEMP_DIR/$context/$VAR_NAME"
        CONTEXT_COUNTS[$i]=$((CONTEXT_COUNTS[$i] + 1))
        TOTAL_VAR_COUNT=$((TOTAL_VAR_COUNT + 1))
      fi
    done < "$file"
  else
    echo "Warning: $file not found, skipping"
  fi
done

# Display summary of variables by context
echo "Found $TOTAL_VAR_COUNT total environment variables to sync."
echo "Distribution across contexts:"
for i in "${!CONTEXTS[@]}"; do
  context="${CONTEXTS[$i]}"
  count=${CONTEXT_COUNTS[$i]}
  echo "- $context: $count variables"
  
  # Warn if context exceeds CircleCI's 100 variable limit
  if [ $count -gt 100 ]; then
    echo "  ⚠️ WARNING: $context exceeds CircleCI's 100 variable limit! ($count variables)"
  fi
  
  # Show variable names in each context if not too many
  if [ $count -gt 0 ] && [ $count -le 20 ]; then
    echo "  Variables in this context:"
    ls -1 "$TEMP_DIR/$context" | while read var; do
      echo "  - $var"
    done
  elif [ $count -gt 20 ]; then
    echo "  First 10 variables in this context:"
    ls -1 "$TEMP_DIR/$context" | head -10 | while read var; do
      echo "  - $var"
    done
    echo "  ... and $((count - 10)) more"
  fi
done

# Confirmation
read -p "Continue with sync to CircleCI contexts? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Operation cancelled."
  rm -rf "$TEMP_DIR"
  exit 1
fi

# Add retry functionality for API operations
retry_command() {
  local max_attempts=3
  local attempt=1
  local timeout=5
  local command=$1
  
  while [ $attempt -le $max_attempts ]; do
    if eval "$command"; then
      return 0
    else
      echo "Command failed, attempt $attempt of $max_attempts. Retrying in $timeout seconds..."
      sleep $timeout
      attempt=$((attempt + 1))
    fi
  done
  
  echo "Command failed after $max_attempts attempts"
  return 1
}

# Process each context
TOTAL_FAILED=0

for i in "${!CONTEXTS[@]}"; do
  context="${CONTEXTS[$i]}"
  count=${CONTEXT_COUNTS[$i]}
  
  if [ $count -eq 0 ]; then
    echo "Skipping empty context: $context"
    continue
  fi
  
  # Check if context exists and create if needed
  echo "Checking if context '$context' exists..."
  
  # Try to create the context - if it exists, this will fail but that's okay
  circleci context create --org-id "$CIRCLECI_ORG_ID" "$context" > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo "Created context $context."
  else
    echo "Context $context already exists."
  fi
  
  # Add variables to context
  echo "Adding variables to CircleCI context '$context'..."
  COUNTER=0
  FAILED=0
  
  for var_file in $(ls -1 "$TEMP_DIR/$context"); do
    COUNTER=$((COUNTER + 1))
    echo "[$COUNTER/$count] Adding $var_file to $context..."
    
    # Store the secret using circleci CLI with the new command syntax
    if ! retry_command "cat '$TEMP_DIR/$context/$var_file' | circleci context store-secret --org-id '$CIRCLECI_ORG_ID' '$context' '$var_file'"; then
      echo "Failed to store $var_file in $context. Continuing with other variables."
      FAILED=$((FAILED + 1))
    fi
  done
  
  echo "Completed context '$context': $((count - FAILED))/$count variables synced successfully."
  TOTAL_FAILED=$((TOTAL_FAILED + FAILED))
done

# Clean up
rm -rf "$TEMP_DIR"

if [ $TOTAL_FAILED -eq 0 ]; then
  echo "✅ All environment variables synced successfully to CircleCI contexts!"
else
  echo "⚠️ Sync completed with $TOTAL_FAILED failures out of $TOTAL_VAR_COUNT variables."
  echo "You may need to manually add the failed variables through the CircleCI web interface."
fi

# Provide instructions for using multiple contexts in CircleCI workflows
echo
echo "💡 To use these contexts in CircleCI workflows, update your .circleci/config.yml files:"
echo "Example:"
echo "  jobs:"
echo "    build:"
echo "      context:"
echo "        - $PREFIX-core"
echo "        - $PREFIX-services"
echo "      # ... rest of job configuration"
echo
echo "You can specify multiple contexts for a job and CircleCI will merge them."