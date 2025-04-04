# Posey CI/CD Setup

#### Integration - Circle CI
We use [circleci][https://circleci.com/docs/] for continuous integration, congigured in `.circleci`.

#### Deployment - Argo CD
Our continuous deployment is powered by [ArgoCD][https://argo-cd.readthedocs.io/en/stable/], setup in `k8s/argo`. The core configuration is managed by the `root-argo-config` application, which acts as an "App of Apps", deploying other application manifests.

### Environment
For local develoment, sensitive information is currently stored in .env files (eventually we need to move to a centralized secrets manager, possibly github).

Since CircleCI and ArgoCD both rely on information stored in .env files. We have a syatem setup to sync the from .env values as secrets:
- `yarn sync:secrets` will will copy the values from ALL of our .env files and pushes them to matching secrets in CircleCI & ArgoCD
- `yarn sync:secrets:ci` Sync .env just to circlci contexts
- `yarn sync:secrets:cd` Sync .env just to argo sealed secrets


## Application Setup
To add a new application to our CI/CD flow, you will need to take a couple of steps:
- Create a new CircleCI Orb and add it to `.circleci/orbs` (if custom CI logic is needed).
- Create a Helm chart for the application in `k8s/charts`.
- Add an Argo CD application manifest to `k8s/argo/apps` or `k8s/argo/services`. This manifest tells Argo CD how to deploy the application, typically by pointing to the Helm chart created in the previous step. The `root-argo-config` application will automatically detect and deploy this new application manifest.
- Create a Helm chart in `k8s/charts`.

Optionally, if you need to expose the application externally:
- Create an Ingress resource in `k8s/ingresses`. We use `ingress-nginx` as our Ingress controller. This resource defines how traffic, typically for a specific hostname, should be routed to your application's service.
- Don't forget to create a DNS A record (e.g., in Cloudflare) pointing to the correct External IP address:
  - **For services exposed directly via LoadBalancer (e.g., databases):** Point the DNS A record to the unique External IP of *that specific service*. These services should be deployed in the `posey` namespace and follow the naming convention `posey-<service-name>`. Get the IP using:
    ```bash
    kubectl get service posey-<service-name> -n posey -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 
    ```
    (Replace `<service-name>` with the actual service name, e.g., `postgres`.)
  - **For web applications exposed via Ingress (e.g., `argo.posey.ai`):** Point the DNS A record to the **shared** External IP of the `ingress-nginx-controller` service. Get it using:
    ```bash
    kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
    ```
    (This IP is used for all hostnames managed by the Ingress controller).

## Monorepo Structure
Our monorepo structure is divided into an idea of "Applications" and "Services". Be sure to pick an appropriate location within `/apps` or `/services` depending on what you are building.

### Applications
Web, Mobile, Desktop and other applications that have direct interaction with user are store in `/apps`

### Services
API, Databases and other services like our MCP Server all live ins `/services`
