# Posey Platform - Argo CD Configuration

This directory contains the Argo CD configurations for the Posey AI Platform.

## Directory Structure

- `applications/`: Contains individual Argo CD Application definitions for each service
- `projects/`: Contains Argo CD Project definitions

## Setup Instructions

### 1. Install Argo CD on DigitalOcean

You can use the DigitalOcean 1-Click install option or install manually with:

```bash
# Install Argo CD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for Argo CD to be ready
kubectl wait --namespace argocd \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=argocd-server \
  --timeout=300s
```

### 2. Access the Argo CD UI

```bash
# Port forward to access Argo CD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get the initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Then open a browser and go to http://localhost:8080

### 3. Apply the Argo CD configurations

```bash
# Apply the Project definition
kubectl apply -f argocd/projects/posey.yaml

# Apply Application definitions
kubectl apply -f argocd/applications/
```

### 4. GitHub Repository Secrets

To enable the GitHub Actions workflow to sync with Argo CD, add the following secrets to your GitHub repository:

- `ARGOCD_SERVER`: The URL of your Argo CD server (e.g., `argocd.example.com`)
- `ARGOCD_PASSWORD`: The password for the Argo CD admin user
- `DO_API_TOKEN`: Your DigitalOcean API token for container registry access
- `DO_REGISTRY_NAME`: Your DigitalOcean container registry name

You can set these secrets in your GitHub repository settings under "Settings" > "Secrets and variables" > "Actions".

### 5. Configuration for CI/CD Integration

For a hybrid approach, you can:

1. Keep GitHub Actions for building and pushing Docker images
2. Use Argo CD for deployment and synchronization

Update your GitHub Actions workflow to:
- Only build and push images
- Trigger Argo CD sync after image push (optional)

Example GitHub Actions workflow step:

```yaml
- name: Trigger Argo CD sync
  run: |
    # Install argocd CLI
    curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
    chmod +x argocd
    
    # Login to Argo CD
    ./argocd login <ARGOCD_SERVER> --username admin --password ${{ secrets.ARGOCD_PASSWORD }} --insecure
    
    # Sync applications
    ./argocd app sync posey-agents
    ./argocd app sync posey-auth
    # ... sync other apps
```

## Best Practices

1. **Image Versioning**: Use semantic versioning for your Docker images
2. **Health Checks**: Configure appropriate health checks for each application
3. **Resource Management**: Set appropriate resource requests and limits
4. **Secret Management**: Use a secret management solution like Sealed Secrets or Vault

## Troubleshooting

If you encounter synchronization issues:

1. Check the Argo CD UI for detailed sync status
2. Run `kubectl logs -n argocd deployment/argocd-application-controller` for controller logs
3. Use `argocd app get <APP_NAME>` for detailed application status

For more information, visit the [Argo CD documentation](https://argo-cd.readthedocs.io/). 