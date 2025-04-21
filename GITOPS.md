# Posey CI/CD Setup

#### Integration - Circle CI
We use [CircleCI](https://circleci.com/docs/) for continuous integration, configured in `.circleci`. Our setup uses dynamic configurations and path filtering to determine which workflows run based on changed files.

#### Deployment - Argo CD
Our continuous deployment is powered by [ArgoCD](https://argo-cd.readthedocs.io/en/stable/), setup in `k8s/argo`. The core configuration is managed by the `root-argo-config` application, which acts as an "App of Apps", deploying other application manifests.

### Environment Secrets
For local development, sensitive information is stored in `.env` files (e.g., `.env`, `services/core/.env`).

Since CircleCI and ArgoCD both rely on these secrets, we have a system to sync them:
- Run `yarn sync:secrets` to update secrets in **both** CircleCI Contexts and ArgoCD (as SealedSecrets). This command executes the following sub-scripts:
  - `yarn sync:secrets:ci` (using `lib/scripts/sync-secrets-circleci.sh`): Updates CircleCI Contexts based on `.env` files mapped in the script (`posey-prod-core`, `posey-prod-data`, etc.).
  - `yarn sync:secrets:cd` (using `lib/scripts/sync-secrets-k8.sh`): Creates/updates ArgoCD SealedSecret manifests in `k8s/secrets/env/` based on `.env` files mapped in the script.

**Important:** Remember to run `yarn sync:secrets` and commit the resulting changes (especially the updated `*-sealed.yaml` files in `k8s/secrets/env/`) whenever you add or modify secrets in the relevant `.env` files.

## Application Setup
To add a new application or service to our CI/CD flow, follow these steps:

1.  **Create Helm Chart:** Create a Helm chart for the application in the appropriate subdirectory within `k8s/charts` (e.g., `k8s/charts/services/core/my-new-service`). Ensure it defines necessary resources like Deployment, Service, etc., and uses values for configuration (ports, image tags, secret names).
2.  **Create CircleCI Orb (Optional):** If the application requires custom CI logic (beyond simple building/pushing), create a new CircleCI Orb in `.circleci/orbs` (e.g., `.circleci/orbs/service-my-new-service-orb.yml`). Reference the `common` orb (`posey/common@<version>`) for shared executors and commands.
3.  **Update CircleCI Configuration:**
    *   **`.circleci/config.yml`:** Modify the `path-filtering/filter` job's `mapping:` section. Add entries linking file paths related to your new service (e.g., `services/core/my-new-service/.*`) to a new pipeline parameter (e.g., `run-my-new-service-workflow true`). Also map changes to your new orb file if you created one.
    *   **`.circleci/continue_config.yml`:**
        *   Define the new pipeline parameter (e.g., `run-my-new-service-workflow: false`).
        *   If you created a custom orb, add it to the `orbs:` section (referencing the `posey/` namespace).
        *   Add a new workflow (or add a job to an existing one) conditioned on your new pipeline parameter (`when: << pipeline.parameters.run-my-new-service-workflow >>`). This workflow should use the appropriate job(s) (either from your new orb or a common orb like `common/build-docker`) to build and deploy your service. Make sure to provide the correct CircleCI Contexts (e.g., `posey-prod-core`, `posey-prod-services`) needed for the job.
4.  **Publish Orbs (If Modified/Created):** Run `yarn publish:orbs` (or `patch`/`minor`/`major` variants). This script (`lib/scripts/publish-orbs-local.sh`) publishes all local orbs in `.circleci/orbs` to the CircleCI registry and automatically updates the orb version references in `.circleci/continue_config.yml`. Commit the changes to `continue_config.yml`.
5.  **Add Argo CD Application Manifest:** Create an Argo CD `Application` manifest YAML file in the appropriate subdirectory within `k8s/argo` (e.g., `k8s/argo/services/core/my-new-service-application.yaml`). This manifest tells Argo CD how to deploy the application, pointing to the Helm chart created in Step 1. The `root-argo-config` application will automatically detect and deploy this new application manifest.

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
API, Databases and other services like our MCP Server all live in `/services`
