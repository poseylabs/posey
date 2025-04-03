# Posey Couchbase

This directory contains the Couchbase database configuration for Posey.

## Overview

Couchbase is used as a document database for storing and retrieving structured data within Posey.

## Docker Compose Deployment

To run Couchbase using Docker Compose:

```bash
cd data/couchbase
docker-compose up -d
```

The Couchbase UI will be available at http://localhost:8091.

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster running (local or remote)
- kubectl configured properly
- Docker installed (for local builds)

### Deployment Steps

1. Deploy Couchbase to Kubernetes:

```bash
# From the couchbase directory
yarn deploy
```

2. Verify the deployment:

```bash
yarn verify
```

3. Connect to Couchbase:

```bash
# Set up port forwarding
yarn port-forward
```

The Couchbase UI will be available at http://localhost:8091.

### Initial Setup

After the first deployment, you need to initialize Couchbase:

1. Access the web UI using port forwarding
2. Follow the setup wizard to:
   - Create a new cluster
   - Configure disk storage
   - Set up memory quotas
   - Create the default bucket "posey"
   - Set admin username and password (default: admin/password)

### Useful Commands

```bash
# Build a local Docker image
yarn build:local

# Deploy to Kubernetes
yarn deploy

# Port forward for local access
yarn port-forward

# Check status
yarn verify

# Debug issues
yarn debug

# Delete deployment
yarn clean

# Redeploy
yarn redeploy
```

## Configuration

The default settings:
- Web UI: Port 8091
- Data service: Port 11210
- Query service: Port 8093
- Search service: Port 8094
- API service: Port 8092
- Username: admin
- Password: password
- Bucket: posey 