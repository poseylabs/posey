# Couchbase Kubernetes Configuration

This directory contains Kubernetes manifests for deploying Couchbase on Kubernetes.

## Manifest Files

- `namespace.yaml`: Defines the Kubernetes namespace
- `couchbase-pvc.yaml`: Persistent Volume Claim for Couchbase data
- `couchbase-deployment.yaml`: Couchbase deployment configuration
- `couchbase-service.yaml`: Service to expose Couchbase within the cluster

## Deployment

To deploy Couchbase, use:

```bash
kubectl apply -k .
```

or apply each file individually:

```bash
kubectl apply -f namespace.yaml
kubectl apply -f couchbase-pvc.yaml
kubectl apply -f couchbase-deployment.yaml
kubectl apply -f couchbase-service.yaml
```

## Access Couchbase

After deployment, the Couchbase web UI is available at port 8091. To access it:

1. Set up port forwarding:
   ```bash
   kubectl port-forward service/posey-couchbase 8091:8091 -n posey
   ```

2. Access the UI at: http://localhost:8091

## Initial Setup

After the first deployment, you need to initialize Couchbase:

1. Access the web UI using port forwarding
2. Follow the setup wizard to:
   - Create a new cluster
   - Configure disk storage
   - Set up memory quotas
   - Create the default bucket "posey"
   - Set admin username and password

## Configuration

The default settings:
- Web UI: Port 8091
- Data service: Port 11210
- Query service: Port 8093
- Search service: Port 8094
- API service: Port 8092

You can adjust resource limits and requests in the `couchbase-deployment.yaml` file based on your needs. 