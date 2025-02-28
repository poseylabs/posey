#!/bin/bash
set -e

# Wait for Couchbase to be ready
until curl -s http://couchbase:8091/pools > /dev/null; do
    echo "Waiting for Couchbase to start..."
    sleep 3
done

# Initialize the cluster
curl -v -X POST http://couchbase:8091/pools/default \
    -d memoryQuota=512 \
    -d indexMemoryQuota=256

# Setup services
curl -v http://couchbase:8091/node/controller/setupServices \
    -d services=kv%2Cn1ql%2Cindex

# Setup credentials
curl -v http://couchbase:8091/settings/web \
    -d port=8091 \
    -d username=$COUCHBASE_USER \
    -d password=$COUCHBASE_PASSWORD

# Setup bucket
curl -v -X POST http://couchbase:8091/pools/default/buckets \
    -u $COUCHBASE_USER:$COUCHBASE_PASSWORD \
    -d name=$COUCHBASE_BUCKET \
    -d bucketType=couchbase \
    -d ramQuota=128 \
    -d flushEnabled=1