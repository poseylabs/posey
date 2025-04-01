#!/bin/bash

# Auto-generated port forwarding script

kubectl port-forward service/postgres 3333:3333 -n posey &
kubectl port-forward service/couchbase 8091:8091 -n posey &
kubectl port-forward service/couchbase 8092:8092 -n posey &
kubectl port-forward service/couchbase 8093:8093 -n posey &
kubectl port-forward service/couchbase 8094:8094 -n posey &
kubectl port-forward service/couchbase 11210:11210 -n posey &
kubectl port-forward service/qdrant 6334:6334 -n posey &
kubectl port-forward service/posey-supertokens 3567:3567 -n posey &
kubectl port-forward service/posey-mcp 5050:5050 -n posey &
kubectl port-forward service/posey-agents 5555:5555 -n posey &
kubectl port-forward service/posey-auth 9999:9999 -n posey &
kubectl port-forward service/posey-cron 2222:2222 -n posey &
kubectl port-forward service/posey-voyager 7777:7777 -n posey &

echo "Port forwarding started. Press Ctrl+C to stop."
trap "kill 0" EXIT
wait
