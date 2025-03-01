#!/bin/bash
# port-forward.sh - Script to port-forward Posey services to localhost
# Usage: ./port-forward.sh [options]
# Options:
#   --service=SERVICE_NAME    Port-forward a specific service (mcp, auth, voyager, grafana)
#   --all                     Port-forward all services
#   --core                    Port-forward core services (mcp, auth, voyager)
#   --db                      Port-forward databases (postgres, qdrant, couchbase)
#   --monitoring              Port-forward monitoring services (grafana)
#   --release=RELEASE_NAME    Helm release name (default: posey)
#   --background              Run port-forwarding in background
#   --help                    Show this help message

set -e

# Default values
RELEASE_NAME="posey"
NAMESPACE="default"
SERVICE=""
FORWARD_ALL=false
FORWARD_CORE=false
FORWARD_DB=false
FORWARD_MONITORING=false
BACKGROUND=false

# Parse command line arguments
for i in "$@"; do
  case $i in
    --service=*)
      SERVICE="${i#*=}"
      shift
      ;;
    --all)
      FORWARD_ALL=true
      shift
      ;;
    --core)
      FORWARD_CORE=true
      shift
      ;;
    --db)
      FORWARD_DB=true
      shift
      ;;
    --monitoring)
      FORWARD_MONITORING=true
      shift
      ;;
    --release=*)
      RELEASE_NAME="${i#*=}"
      shift
      ;;
    --namespace=*)
      NAMESPACE="${i#*=}"
      shift
      ;;
    --background)
      BACKGROUND=true
      shift
      ;;
    --help)
      echo "Usage: ./port-forward.sh [options]"
      echo "Options:"
      echo "  --service=SERVICE_NAME    Port-forward a specific service (mcp, auth, voyager, grafana)"
      echo "  --all                     Port-forward all services"
      echo "  --core                    Port-forward core services (mcp, auth, voyager)"
      echo "  --db                      Port-forward databases (postgres, qdrant, couchbase)"
      echo "  --monitoring              Port-forward monitoring services (grafana)"
      echo "  --release=RELEASE_NAME    Helm release name (default: posey)"
      echo "  --namespace=NAMESPACE     Kubernetes namespace (default: default)"
      echo "  --background              Run port-forwarding in background"
      echo "  --help                    Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $i"
      exit 1
      ;;
  esac
done

# Get service ports from kubectl
function get_service_port() {
  local service=$1
  local port
  port=$(kubectl get svc "$RELEASE_NAME-$service" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null || echo "")
  echo "$port"
}

# Function to port-forward a service
function forward_service() {
  local service=$1
  local port=$2
  local cmd="kubectl port-forward svc/$RELEASE_NAME-$service -n $NAMESPACE $port:$port"
  
  echo "🔗 Forwarding $service to http://localhost:$port"
  
  if [ "$BACKGROUND" = true ]; then
    $cmd &
    echo "   Process running in background with PID $!"
  else
    echo "   Press Ctrl+C to stop"
    $cmd
  fi
}

# Forward a specific service
function forward_specific_service() {
  local service_name=$1
  
  case $service_name in
    mcp)
      local port=$(get_service_port "mcp")
      [ -z "$port" ] && port=5050
      forward_service "mcp" "$port"
      ;;
    auth)
      local port=$(get_service_port "auth")
      [ -z "$port" ] && port=9999
      forward_service "auth" "$port"
      ;;
    voyager)
      forward_service "voyager" "3030"
      ;;
    agents)
      local port=$(get_service_port "agents")
      [ -z "$port" ] && port=3001
      forward_service "agents" "$port"
      ;;
    cron)
      forward_service "cron" "3040"
      ;;
    supertokens)
      local port=$(get_service_port "supertokens")
      [ -z "$port" ] && port=3567
      forward_service "supertokens" "$port"
      ;;
    postgres)
      local port=$(get_service_port "postgres")
      [ -z "$port" ] && port=3333
      forward_service "postgres" "$port"
      ;;
    qdrant)
      local port=$(get_service_port "qdrant")
      [ -z "$port" ] && port=1111
      forward_service "qdrant" "$port"
      ;;
    couchbase)
      forward_service "couchbase" "8091"
      ;;
    grafana)
      forward_service "grafana" "3000"
      ;;
    *)
      echo "⚠️ Unknown service: $service_name"
      echo "Available services: mcp, auth, voyager, agents, cron, supertokens, postgres, qdrant, couchbase, grafana"
      exit 1
      ;;
  esac
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
  echo "❌ kubectl could not be found. Please install kubectl first."
  exit 1
fi

# Check if the release exists
if ! kubectl get deployment "$RELEASE_NAME-mcp" -n "$NAMESPACE" &> /dev/null; then
  echo "❌ Release '$RELEASE_NAME' not found. Please check if the Helm release is installed."
  exit 1
fi

# Forward services based on options
if [ -n "$SERVICE" ]; then
  forward_specific_service "$SERVICE"
elif [ "$FORWARD_ALL" = true ]; then
  echo "🚀 Forwarding all services..."
  
  # We need to run these in background except the last one
  BACKGROUND=true
  
  # Core services
  forward_specific_service "mcp"
  forward_specific_service "auth"
  forward_specific_service "voyager"
  forward_specific_service "agents"
  forward_specific_service "cron"
  
  # Databases
  forward_specific_service "postgres"
  forward_specific_service "qdrant"
  
  # For the last one, we set BACKGROUND=false to keep the script running
  BACKGROUND=false
  forward_specific_service "grafana"
  
elif [ "$FORWARD_CORE" = true ]; then
  echo "🚀 Forwarding core services..."
  
  # We need to run these in background except the last one
  BACKGROUND=true
  
  forward_specific_service "mcp"
  forward_specific_service "auth"
  
  BACKGROUND=false
  forward_specific_service "voyager"
  
elif [ "$FORWARD_DB" = true ]; then
  echo "🚀 Forwarding databases..."
  
  BACKGROUND=true
  forward_specific_service "postgres"
  forward_specific_service "qdrant"
  
  BACKGROUND=false
  forward_specific_service "couchbase"
  
elif [ "$FORWARD_MONITORING" = true ]; then
  echo "🚀 Forwarding monitoring services..."
  forward_specific_service "grafana"
else
  echo "⚠️ No forwarding option selected. Use --all, --core, --db, --monitoring, or --service=SERVICE_NAME"
  exit 1
fi

echo "✅ Done!" 