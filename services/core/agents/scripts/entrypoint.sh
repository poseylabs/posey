#!/bin/bash
echo "--- Entrypoint Script Started ---"
set -e

# Debug: Print service type and environment
echo "Environment variables:"
echo "RUN_MIGRATIONS=$RUN_MIGRATIONS"
echo "DROP_TABLES=$DROP_TABLES"
echo "RUN_SEEDS=$RUN_SEEDS"
echo "DOWNLOAD_EMBEDDINGS=$DOWNLOAD_EMBEDDINGS"
echo "PYTHONPATH=$PYTHONPATH"
echo "ALLOWED_ORIGINS=$ALLOWED_ORIGINS"
echo "ALLOWED_HOSTS=$ALLOWED_HOSTS"
echo "PYTHON_PATH=$PYTHONPATH"

echo "POSTGRES_DSN_POSEY=$POSTGRES_DSN_POSEY"
echo "POSTGRES_USER=$POSTGRES_USER"
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "POSTGRES_HOST=$POSTGRES_HOST"
echo "POSTGRES_DB_POSEY=$POSTGRES_DB_POSEY"

# Wait for databases to be ready
echo "Waiting for databases to be ready..."

# Wait for PostgreSQL
echo "--- Changing to /app directory ---"
cd /app
echo "--- In /app directory --- Check critical paths:"
echo "Main app directory (/app/service):"
ls -l /app/service
echo "Service scripts directory (/app/service/scripts):"
ls -l /app/service/scripts
echo "App scripts directory (/app/service/app/scripts):"
ls -l /app/service/app/scripts
echo "--- Finished Path Checks ---"

echo "--- Checking PostgreSQL Connection --- START ---"
while ! python /app/service/app/scripts/check_db.py; do
    echo "Waiting for PostgreSQL at $POSTGRES_HOST... (python check_db.py failed)"
    sleep 3
done
echo "--- Checking PostgreSQL Connection --- END ---"

echo "PostgreSQL is ready!"

# Check required environment variables
if [ -z "$COUCHBASE_ADMIN_URL" ]; then
    echo "Error: COUCHBASE_ADMIN_URL environment variable is not set"
    exit 1
fi

echo "--- Checking Couchbase Connection --- START ---"
# Wait for Couchbase
until curl -s "$COUCHBASE_ADMIN_URL/pools" > /dev/null; do
    echo "Waiting for Couchbase at $COUCHBASE_ADMIN_URL... (curl failed or timed out)"
    sleep 3
done
echo "--- Checking Couchbase Connection --- END ---"

# Drop tables if enabled
if [ "$DROP_TABLES" = "true" ]; then
    echo "WARNING: DROP_TABLES is enabled - all tables will be dropped!"
    read -t 5 -p "You have 5 seconds to cancel (Ctrl+C)..." || true
    echo "Proceeding with table drop..."
fi

# Initialize databases if needed
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."

    echo "Running Alembic upgrade..."

    cd /app/service
    
    # --- IMPORTANT FIX --- 
    # Unset the external DSN var before running upgrade inside the container.
    # This forces env.py to use the internal POSTGRES_DSN_POSEY.
    echo "Ensuring internal DSN is used for container migrations..."
    unset POSTGRES_DSN_POSEY_EXTERNAL
    # --------------------
    
    echo "--- Running Alembic Upgrade --- START ---"
    alembic upgrade head
    echo "--- Running Alembic Upgrade --- END ---"
    
    cd /app # Change back to original directory

else
    echo "Skipping database migrations..."
fi

if [ "$DOWNLOAD_EMBEDDINGS" = "true" ]; then
    # Download embedding model at runtime when env vars are available
    echo "Downloading embedding model..."
    python -c "from fastembed import TextEmbedding; import os; TextEmbedding(model_name=os.getenv('EMBEDDING_MODEL', 'BAAI/bge-large-en-v1.5'), cache_dir=os.getenv('EMBEDDING_CACHE_DIR', '/app/models'))"
    echo "Embedding model downloaded successfully!"
else
    echo "Skipping embedding model download..."
fi

# Start the application
# Debug: Print current directory and files
echo "Current directory: $(pwd)"
ls -la

# Trap SIGTERM and SIGINT
trap 'kill -TERM $PID' TERM INT

echo "Starting API server..."
uvicorn app.main:app --host 0.0.0.0 --port 5555 &
PID=$!
wait $PID

echo "--- Script finished or Uvicorn exited, sleeping infinitely to keep container alive for debugging ---"
sleep infinity
