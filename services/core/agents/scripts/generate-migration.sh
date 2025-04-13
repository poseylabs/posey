#!/bin/bash
set -e

# Navigate to the service root directory first
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SERVICE_DIR=$(dirname "$SCRIPT_DIR") # Go up one level to service root
cd "$SERVICE_DIR"
echo "Running from service directory: $(pwd)"

# --- Load .env file if it exists --- 
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE"
    # Use set -a to export all variables read from .env
    set -a 
    source "$ENV_FILE"
    set +a
    # Verify external DSN is loaded (optional debug)
    # echo "POSTGRES_DSN_POSEY_EXTERNAL=${POSTGRES_DSN_POSEY_EXTERNAL}" 
else
    echo "Warning: .env file not found at $(pwd)/$ENV_FILE"
fi
# ------------------------------------

# Default message if none provided
MESSAGE="Auto-generated migration"

# Parse arguments - looking for -m
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -m|--message)
        MESSAGE="$2"
        shift # past argument
        shift # past value
        ;;
        *)    # unknown option
        shift # past argument
        ;;
    esac
done

echo "Generating Alembic migration with message: '$MESSAGE'"

# Check if alembic.ini exists in ./app or ./
# (Script is already in SERVICE_DIR, so check relative paths)
ALEMBIC_CONFIG_PATH=""
if [ -f "app/alembic.ini" ]; then
    ALEMBIC_CONFIG_PATH="app/alembic.ini"
    # No cd needed if running from service root and using -c
elif [ -f "alembic.ini" ]; then
     ALEMBIC_CONFIG_PATH="alembic.ini"
else
    echo "Error: Could not find alembic.ini in ./app or ."
    exit 1
fi

# Ensure PYTHONPATH includes the app directory
# This helps Alembic find your models etc.
export PYTHONPATH=$PYTHONPATH:$(pwd)/app 
export PYTHONPATH=$PYTHONPATH:$(pwd) # Add service root too
echo "PYTHONPATH=$PYTHONPATH"

# Run the alembic command using the located config file
# Alembic will use the environment variables loaded from .env
echo "Running: alembic -c $ALEMBIC_CONFIG_PATH revision --autogenerate -m \"$MESSAGE\""
alembic -c "$ALEMBIC_CONFIG_PATH" revision --autogenerate -m "$MESSAGE"

echo "Migration generated successfully."

# Optional: Make the script executable immediately after creation (though this is usually done via git)
# chmod +x "$SCRIPT_DIR/generate-migration.sh" 