# Posey Platform Development Guide

This document explains the development setup for the Posey Platform, focusing on how to interact with services locally within our Kubernetes-based GitOps workflow.

## Architecture Overview

The Posey Platform consists of several components deployed within a Kubernetes cluster, managed via Helm charts and ArgoCD:

1.  **Data Services** (primarily defined in `services/data/` and deployed via charts in `k8s/charts/services/data/`)
    *   PostgreSQL: Main relational database
    *   Qdrant: Vector database for semantic search
    *   Couchbase: Document database

2.  **Core Services** (primarily defined in `services/core/` and deployed via charts in `k8s/charts/services/core/`)
    *   Auth: Authentication service (using SuperTokens)
    *   MCP: Main communication protocol service
    *   Cron: Scheduled task service
    *   Agents: AI agent framework (if applicable)
    *   Voyager: Exploration and discovery service (if applicable)
    *   SuperTokens: Core authentication provider instance

## Development Workflow (GitOps via CircleCI & ArgoCD)

Development follows a GitOps approach:

1.  **Code Changes:** Make your code changes in the relevant service directory (e.g., `services/core/auth`).
2.  **Git Commit & Push:** Commit your changes and push them to your feature branch or directly to `main`/`develop` (depending on branching strategy).
3.  **CircleCI Builds:** Pushing changes triggers CircleCI workflows (defined in `.circleci/`) based on path filtering (`.circleci/config.yml`). Relevant jobs (often defined in service-specific Orbs) build Docker images and push them to the registry (e.g., Docker Hub).
4.  **ArgoCD Sync:**
    *   If the changes involve Kubernetes manifests (Helm charts, values, Argo Application manifests in `k8s/`), ArgoCD automatically detects these changes in the Git repository (`main` branch) and syncs the applications, applying the new configurations to the cluster.
    *   If only the Docker image tag needs updating (e.g., using `:latest` or a commit SHA), the CircleCI job might trigger an ArgoCD sync/refresh for the specific application (as seen in `service-auth-orb.yml` using `trigger-argocd-sync.sh`) to ensure the new image is pulled.
5.  **Local Development Cluster:** For local development and testing, you should run a local Kubernetes cluster (e.g., Kind, Minikube, Docker Desktop Kubernetes). Your ArgoCD instance should be configured to deploy to this local cluster (or a dedicated dev namespace in a shared cluster).

**Building Locally (for quick tests):**
While the primary build process is via CircleCI, you might occasionally build an image locally for rapid testing:
```bash
# Example for auth service
docker build -t poseylabs/posey-auth:local-test -f services/core/auth/Dockerfile .
# Note: This doesn't replicate the multi-platform build from CI.
```
Deploying these local builds typically involves manually editing the Kubernetes Deployment manifest (`kubectl edit deployment...`) or updating the ArgoCD Application manifest locally to point to the `local-test` tag temporarily (and avoiding committing that change).

## Accessing Services Locally

While services run within Kubernetes, you can access them on your local machine using:

1.  **Port Forwarding (Primary Method):**
    The easiest way to access services directly from your local machine is using the provided port-forwarding script:
    ```bash
    yarn port-forward # From project root (runs scripts/port-forward-all.sh)
    ```
    This script sets up `kubectl port-forward` commands for all standard services, making them available on `localhost` at their designated ports (see Standard Local Ports below). Keep this script running in a terminal window.

2.  **Ingress (for domain-based access):**
    If you need to test domain-based routing (e.g., `auth.api.posey.ai`) locally:
    *   Ensure your local Kubernetes cluster has an Ingress controller (like `ingress-nginx`) running.
    *   The Helm charts (deployed by ArgoCD) should create the necessary Ingress resources.
    *   You may need to manually update your local `/etc/hosts` file to point the service domains (e.g., `auth.api.posey.ai`) to the IP address of your local Ingress controller service (often `127.0.0.1` if it's port-forwarded or using host networking). The `./update-ingress.sh` script *might* assist with this, but verify its current functionality.

3.  **Direct Pod/Service Access (Advanced):**
    You can use `kubectl exec` to run commands inside a pod or `kubectl port-forward` manually for specific services if the main script isn't suitable.

## Standard Local Ports (via `yarn port-forward`)

These are the ports exposed on `localhost` when `yarn port-forward` is running:

### Data Services
- PostgreSQL: `localhost:3333`
- Couchbase: `localhost:8091`
- Qdrant: `localhost:1111`

### Core Services
- Auth: `localhost:9999`
- Cron: `localhost:2222` *(Verify if still relevant)*
- MCP: `localhost:5050`
- SuperTokens: `localhost:3567`
- *(Verify Agents/Voyager ports if applicable)*

*Note: These are the ports forwarded to your local machine. The ports used *inside* the cluster might differ.*

## Production Deployment

Production follows the same GitOps flow, targeting the production Kubernetes cluster (e.g., on DigitalOcean). ArgoCD monitors the `main` branch and applies the Helm charts defined in `k8s/`. DNS is configured to point to the production Ingress controller's LoadBalancer IP or specific LoadBalancer IPs for directly exposed services. 