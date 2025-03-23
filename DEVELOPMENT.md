# Posey Platform Development Guide

This document explains the development setup for the Posey Platform, including both data services and application services.

## Architecture Overview

The Posey Platform consists of two main components:

1. **Data Services** (in `/data` directory)
   - PostgreSQL: Main relational database
   - Qdrant: Vector database for semantic search
   - GraphQL: API layer for data access
   - Couchbase: Document database for specific data needs

2. **Application Services** (in `/services` directory)
   - Agents: AI agent framework
   - Auth: Authentication service
   - Cron: Scheduled task service
   - MCP: Main communication protocol service
   - SuperTokens: Authentication provider
   - Voyager: Exploration and discovery service

## Development Workflow

### Building and Deploying

We maintain separate build and deploy scripts for data and application services due to their logical separation, but they all get deployed to the same Kubernetes namespace.

**Data Services:**
```bash
cd /data
yarn build:local    # Build Docker images
yarn deploy:local   # Deploy to local Kubernetes
```

**Application Services:**
```bash
cd /services
yarn build:local    # Build Docker images
yarn deploy:local   # Deploy to local Kubernetes
```

### Unified Access

While the build/deploy scripts are separate, we have **unified ingress and access** through:

1. **NodePorts:** All services use NodePort for consistent access
2. **Port Forwarding:** A unified script for port forwarding
3. **Ingress:** Single nginx ingress configuration

### Accessing Services

There are several ways to access the services:

1. **Ingress (for DNS setup):**
   ```bash
   ./update-ingress.sh  # From project root
   ```
   
   This sets up the ingress and gives you the necessary `/etc/hosts` entries.

2. **Direct NodePort Access:**
   Services are available directly via NodePorts if needed.

## Standard Ports

### Data Services
- PostgreSQL: `localhost:3333`
- Couchbase: `localhost:8091`
- GraphQL: `localhost:4444`
- Qdrant: `localhost:1111`

### Application Services
- Agents: `localhost:5555`
- Auth: `localhost:9999`
- Cron: `localhost:2222`
- MCP: `localhost:5050`
- SuperTokens: `localhost:3567`
- Voyager: `localhost:7777`

## Production Deployment

In production, all services are deployed to a single Digital Ocean Kubernetes cluster with proper DNS configuration using the same ingress controller.

The local setup mirrors this production configuration, with the exception of using NodePorts and port forwarding for local access instead of LoadBalancers. 