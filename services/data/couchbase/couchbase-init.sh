#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "--- Custom Couchbase Entrypoint Started ---"

# --- Configuration Variables ---
# Use environment variables, provide defaults for admin credentials
# WARNING: Default admin credentials are insecure. Set COUCHBASE_ADMIN_USER and COUCHBASE_ADMIN_PASSWORD in your environment for production!
CB_ADMIN_USER="${COUCHBASE_ADMIN_USER:-Administrator}"
CB_ADMIN_PASSWORD="${COUCHBASE_ADMIN_PASSWORD:-password}"
CB_INTERNAL_URL="http://127.0.0.1:8091" # Use localhost for internal checks

# Check required application variables
: "${COUCHBASE_BUCKET?Need to set COUCHBASE_BUCKET}"
: "${COUCHBASE_USER?Need to set COUCHBASE_USER}"
: "${COUCHBASE_PASSWORD?Need to set COUCHBASE_PASSWORD}"

CB_RAM_QUOTA="${COUCHBASE_BUCKET_RAM_QUOTA:-256}" # Default RAM quota in MB

echo "Using Couchbase Bucket: $COUCHBASE_BUCKET"
echo "Using Couchbase App User: $COUCHBASE_USER"
echo "Using Couchbase Admin User: $CB_ADMIN_USER"
echo "Using Couchbase RAM Quota: $CB_RAM_QUOTA MB"
# --- End Configuration ---

# Start the original Couchbase entrypoint script in the background
# Assuming the original entrypoint is /entrypoint.sh (common in official images)
echo "Starting original Couchbase entrypoint in background..."
/entrypoint.sh couchbase-server &
CB_PID=$!
echo "Couchbase server process started with PID $CB_PID"

# Wait for Couchbase REST API to be ready
echo "Waiting for Couchbase REST API at $CB_INTERNAL_URL..."
until curl -s --output /dev/null "$CB_INTERNAL_URL/pools"; do
    echo "Couchbase API not ready yet..."
    # Check if the background process is still running
    if ! kill -0 $CB_PID 2>/dev/null; then
        echo "ERROR: Couchbase server process (PID $CB_PID) exited unexpectedly!"
        exit 1
    fi
    sleep 3
done
echo "Couchbase REST API is ready!"

# --- Perform Initial Setup via REST API ---

# Check if Cluster needs initialization (Check for node status)
# A 404 on pools/default often means it's not initialized yet
echo "Checking cluster initialization status..."
INIT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CB_INTERNAL_URL/pools/default")

if [ "$INIT_STATUS" -eq 404 ]; then
    echo "Cluster not initialized. Initializing..."
    # Initialize the node itself (adjust paths if necessary)
    curl -s -X POST "$CB_INTERNAL_URL/nodes/self/controller/settings" \
        -d path="/opt/couchbase/var/lib/couchbase/data" \
        -d index_path="/opt/couchbase/var/lib/couchbase/index" \
        -d eventing_path="/opt/couchbase/var/lib/couchbase/eventing" \
        -d analytics_path="/opt/couchbase/var/lib/couchbase/analytics" \
        -d cbas_path="/opt/couchbase/var/lib/couchbase/cbas"

    # Initialize cluster services (data, index, query, fts) - adjust based on needs
    curl -s -X POST "$CB_INTERNAL_URL/node/controller/setupServices" \
        -d services="kv,index,n1ql,fts" # Add other services like eventing, analytics if needed

    # Set memory quotas (example: same as bucket quota for total)
    curl -s -X POST "$CB_INTERNAL_URL/pools/default" \
        -d memoryQuota="$CB_RAM_QUOTA" \
        -d indexMemoryQuota="$CB_RAM_QUOTA" # Adjust index quota as needed
        # Add quotas for other services if enabled (ftsMemoryQuota, etc.)

    # Set administrator username and password
    curl -s -X POST "$CB_INTERNAL_URL/settings/web" \
        -d port=8091 \
        -d username="$CB_ADMIN_USER" \
        -d password="$CB_ADMIN_PASSWORD"

    echo "Cluster initialization requested. Waiting..."
    sleep 10 # Give Couchbase time to initialize
else
    echo "Cluster already initialized or initialization check inconclusive (Status: $INIT_STATUS). Assuming ready."
fi


# Check if bucket exists
echo "Checking if Couchbase bucket '$COUCHBASE_BUCKET' exists..."
BUCKET_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "$CB_ADMIN_USER:$CB_ADMIN_PASSWORD" "$CB_INTERNAL_URL/pools/default/buckets/$COUCHBASE_BUCKET")

if [ "$BUCKET_STATUS" -eq 404 ]; then
    echo "Bucket '$COUCHBASE_BUCKET' does not exist. Creating..."
    curl -s -u "$CB_ADMIN_USER:$CB_ADMIN_PASSWORD" -X POST "$CB_INTERNAL_URL/pools/default/buckets" \
        -d name="$COUCHBASE_BUCKET" \
        -d ramQuotaMB="$CB_RAM_QUOTA" \
        -d bucketType=couchbase \
        -d replicaNumber=0 # Adjust for multi-node clusters
    echo "Bucket '$COUCHBASE_BUCKET' creation requested. Waiting..."
    sleep 5
else
    echo "Bucket '$COUCHBASE_BUCKET' already exists (Status: $BUCKET_STATUS)."
fi

# Check if user exists
echo "Checking if Couchbase user '$COUCHBASE_USER' exists..."
# Need to URL-encode the username if it contains special characters, but assuming simple names for now.
# USER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "$CB_ADMIN_USER:$CB_ADMIN_PASSWORD" "$CB_INTERNAL_URL/settings/rbac/users/local/$COUCHBASE_USER")

# if [ "$USER_STATUS" -eq 404 ]; then
# Always run the PUT command to create or update the user and ensure correct roles
echo "Ensuring user '$COUCHBASE_USER' exists with correct roles (bucket_full_access, admin)..."

# Assign roles - adjust as needed. 'bucket_admin' or 'bucket_full_access' are common.
# Ensure roles are valid for your Couchbase version.
# Use --data-urlencode for the password field
curl -s -u "$CB_ADMIN_USER:$CB_ADMIN_PASSWORD" -X PUT "$CB_INTERNAL_URL/settings/rbac/users/local/$COUCHBASE_USER" \
    --data-urlencode "password=$COUCHBASE_PASSWORD" \
    -d roles="bucket_full_access[$COUCHBASE_BUCKET],admin" # Grant bucket access AND admin role for UI login
    # Add other roles like 'query_select[*]', 'query_insert[*]' if needed, separated by comma
echo "User '$COUCHBASE_USER' create/update requested."
# Add a small delay/check after creation if needed
sleep 2 
# else
#     echo "User '$COUCHBASE_USER' already exists (Status: $USER_STATUS)."
# fi

echo "--- Couchbase Initial Setup Complete ---"

# Bring the Couchbase server process to the foreground
echo "Bringing Couchbase server (PID $CB_PID) to foreground..."
wait $CB_PID

# If wait exits, log it (should only happen on signal)
CB_EXIT_CODE=$?
echo "Couchbase server process (PID $CB_PID) exited with code $CB_EXIT_CODE."
exit $CB_EXIT_CODE 