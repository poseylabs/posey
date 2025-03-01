# Posey Build and Deployment Scripts

This directory contains scripts to automate building, pushing, and deploying Posey services.

## Docker Image Building and Pushing

### Local Usage

The `build-push-services.sh` script automatically builds and pushes Docker images for all services to the DigitalOcean registry.

#### Basic Usage

```bash
# Build and push all services with the 'latest' tag
./scripts/build-push-services.sh

# Build and push all services with a custom tag
./scripts/build-push-services.sh v1.0.0
```

#### Via NPM/Yarn Scripts

We've added convenience scripts in package.json:

```bash
# Build and push with 'latest' tag
yarn docker:build-push

# Build and push with custom tag
yarn docker:build-push:tag v1.0.0
```

### Automated via GitHub Actions

A GitHub Actions workflow is configured in `.github/workflows/build-push-images.yml` that will automatically:

1. Build and push images when code is pushed to `main` or `develop` branches
2. Tag images automatically based on branch name and timestamp
3. Allow manual triggering with custom tags via workflow dispatch

#### Prerequisites for GitHub Actions

For the GitHub Actions workflow to work, you must set up a repository secret:

- `DIGITALOCEAN_ACCESS_TOKEN`: A DigitalOcean personal access token with read/write access to the container registry

## How It Works

The build script:

1. Automatically discovers all services with Dockerfiles in the `services/` directory
2. Builds Docker images for each service
3. Tags them according to the specified format (`registry.digitalocean.com/posey/posey-{service}:{tag}`)
4. Pushes them to the DigitalOcean registry
5. Provides a summary of successful and failed operations

## Troubleshooting

If you encounter issues:

1. Ensure Docker is running
2. Check you're logged into the DigitalOcean registry with `doctl registry login`
3. Verify that each service has a valid Dockerfile
4. Check for network connectivity to the DigitalOcean registry 