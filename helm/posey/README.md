# Posey Helm Chart

This Helm chart deploys the Posey AI project on Kubernetes.

## Prerequisites

- Kubernetes 1.16+
- Helm 3.0+
- PV provisioner support in the underlying infrastructure (for PostgreSQL storage)

## Getting Started

### Installing the Chart

To install the chart with the release name `posey`:

```bash
helm install posey ./helm/posey
```

### Managing Secrets

This chart requires sensitive data like API keys and database passwords. We've provided a `secrets-values.yaml` template that you should copy and fill with your actual secrets:

```bash
cp helm/posey/secrets-values.yaml my-secrets.yaml
# Edit my-secrets.yaml with your actual secret values
```

Then install the chart using both the default values and your secrets:

```bash
helm install posey ./helm/posey -f helm/posey/values.yaml -f my-secrets.yaml
```

Or use the npm script which automatically includes both files:

```bash
yarn helm
```

**IMPORTANT**: Never commit your secrets file to version control!

### Using a Custom Values File

Create a copy of the default `values.yaml` file and customize it:

```bash
cp helm/posey/values.yaml my-values.yaml
# Edit my-values.yaml with your preferred editor
```

Then, install the chart using your custom values:

```bash
helm install posey ./helm/posey -f my-values.yaml
```

### Upgrading the Chart

```bash
helm upgrade posey ./helm/posey -f my-values.yaml
```

### Uninstalling the Chart

```bash
helm uninstall posey
```

## Configuration

The following table lists the configurable parameters of the Posey chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `core.nodeEnv` | Node environment setting | `"production"` |
| `core.debug` | Debug mode flag | `"false"` |
| `services.postgres.host` | PostgreSQL host | `"posey-postgres"` |
| `services.postgres.port` | PostgreSQL port | `"3333"` |
| `services.postgres.user` | PostgreSQL user | `"postgres"` |
| `databases.postgres.password` | PostgreSQL password | `""` (Must be provided) |
| `databases.postgres.dbPosey` | PostgreSQL database name | `"posey"` |
| `apikeys.*` | Various API keys | `""` (Must be provided) |

## Security Considerations

This chart handles sensitive information like database passwords and API keys. In production environments:

1. Never store secrets in plain text in values files
2. Use sealed secrets, Hashicorp Vault, or a similar solution
3. Consider using Kubernetes Secrets for sensitive values separately:

```bash
kubectl create secret generic api-credentials \
  --from-literal=ANTHROPIC_API_KEY=your-key \
  --from-literal=OPENAI_API_KEY=your-key
```

Then reference these existing secrets in your values file.

## Persistence

This chart uses PersistentVolumeClaims for PostgreSQL data storage. The PVCs are created with the `do-block-storage` StorageClass by default, which should be adjusted for your environment.

## Monitoring & Logging

Health checks are included for the services. For more advanced monitoring, consider integrating with Prometheus and Grafana. 