# Posey CircleCI Orbs

This directory contains CircleCI orbs used in the Posey project. Orbs are reusable packages of CircleCI configuration that can be shared across projects.

## Publishing Strategy

We use a two-stage approach for orbs:

1. **Initial Development**: We use inline orbs defined directly in our configuration files, allowing us to develop and test the orbs without requiring them to be published first.

2. **Production**: Once the orbs are stable, they are published to the CircleCI registry in the `posey` namespace.

## Important Version Notes

When referencing standard CircleCI orbs, use these specific versions:

- `circleci/circleci-cli@0.1.9` - The CircleCI CLI orb (not 2.0.0)
- `circleci/path-filtering@1.0.0`
- `circleci/docker@2.5.0`

Using incorrect versions will result in "Cannot find orb" errors during pipeline execution.

## Automatic Orb Publishing

The orbs in this directory are automatically published to the CircleCI registry whenever changes are pushed to the repository. This is handled by the `.circleci/publish-orbs.yml` workflow, which is triggered when any files in the `.circleci/orbs` directory change.

## Orb Structure

All orbs follow a consistent naming pattern:
- `common-orb.yml`: Contains shared executors and commands used by all other orbs
- `service-*-orb.yml`: Orbs for specific services (auth, cron, etc.)
- `data-*-orb.yml`: Orbs for data services (postgres, couchbase, vector-db)

## Adding New Orbs

To add a new orb:

1. Create a new file in this directory following the naming convention:
   - For a service: `service-[name]-orb.yml`
   - For a data service: `data-[name]-orb.yml`

2. Run the update script to automatically adjust the orb publishing configuration:
   ```bash
   .circleci/scripts/update-and-commit-orb-config.sh
   ```

3. Add an inline version of the orb to `.circleci/continue_config.yml` until the orb is published:
   ```yaml
   orbs:
     # Existing orbs...
     your-new-orb:
       description: "Your new orb description"
       jobs:
         your-job:
           # Job definition here
   ```

4. After the orb is published, update the reference to use the published version:
   ```yaml
   orbs:
     # Existing orbs...
     your-new-orb: posey/your-new-orb@1.0
   ```

## Setting Up Git Hooks (for developers)

To ensure everything stays in sync, we recommend setting up git hooks:

```bash
.circleci/scripts/setup-hooks.sh
```

This will install a pre-push hook that automatically updates the orb publishing configuration when you push changes.

## Manual Updates

If you need to manually update the orb configuration:

```bash
.circleci/scripts/update-and-commit-orb-config.sh
```

This script will run the update process and commit any changes to the repository.

## How It Works

The automatic publishing process works as follows:

1. When changes are pushed to the repository, CircleCI checks if any files in the `.circleci/orbs` directory have changed.
2. If orb files have changed, the `publish-orbs` workflow is triggered.
3. The workflow:
   - Creates the namespace if it doesn't exist
   - Creates each orb if it doesn't exist
   - Publishes all orbs to the registry

This ensures that the orbs in the registry are always in sync with the orbs in the repository. 