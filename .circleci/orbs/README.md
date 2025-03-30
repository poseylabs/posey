# Posey CircleCI Orbs

This directory contains CircleCI orbs used in the Posey project. Orbs are reusable packages of CircleCI configuration that can be shared across projects.

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

2. The orb will be automatically detected and published the next time you push to the repository.

3. Update the `.circleci/continue_config.yml` file to include the new orb in the list:
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

This will install a pre-push hook that ensures the orb configuration is always up-to-date.

## How It Works

The automatic publishing process works as follows:

1. When changes are pushed to the repository, CircleCI checks if any files in the `.circleci/orbs` directory have changed.
2. If orb files have changed, the `publish-orbs` workflow is triggered.
3. The workflow:
   - Creates the namespace if it doesn't exist
   - Creates each orb if it doesn't exist
   - Publishes all orbs to the registry

This ensures that the orbs in the registry are always in sync with the orbs in the repository. 