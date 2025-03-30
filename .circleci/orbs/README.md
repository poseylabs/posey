# Posey CircleCI Orbs

This directory contains CircleCI orbs used in the Posey project. Orbs are reusable packages of CircleCI configuration that can be shared across projects.

## Publishing Strategy

We use a two-stage approach for orbs:

1. **Initial Development**: We use inline orbs defined directly in our configuration files, allowing us to develop and test the orbs without requiring them to be published first.

2. **Production**: Once the orbs are stable, they are published to the CircleCI registry in the `posey` namespace and all inline definitions are removed from the config.

## Current Versions

We now use consistent semantic versioning for all orbs:

- **Common orb**: `posey/common@0.0.7` (production version)
- **All other orbs**: Published as production versions (`0.0.1`) to match the common orb

This approach ensures all orbs follow the same versioning scheme, making it easier to track updates and versions.

CircleCI orbs follow these versioning rules:

- Development versions: `dev:name` format (like `dev:alpha1`) - these are mutable and can be updated
- Production versions: `x.y.z` format (like `0.0.5`) - these are immutable once published

All of our orbs use the production versioning format for consistency.

## Important Version Notes

When referencing standard CircleCI orbs, use these specific versions:

- `circleci/circleci-cli@0.1.9` - The CircleCI CLI orb (not 2.0.0)
- `circleci/path-filtering@1.0.0`
- `circleci/docker@2.5.0`

Using incorrect versions will result in "Cannot find orb" errors during pipeline execution.

## Publishing Orbs Locally (Required First-Time Setup)

Before pushing to CircleCI, you must first publish the orbs locally to set up the namespace and initial orb versions. This is a one-time setup to resolve the chicken-and-egg problem where jobs reference orbs that don't exist yet.

1. Ensure you have the CircleCI CLI installed and configured with an API token:
   ```bash
   # Install CircleCI CLI
   brew install circleci
   
   # Set up API Token (get from CircleCI web UI)
   export CIRCLE_TOKEN='your-circleci-token'
   ```

2. Run the publish script from the repository root:
   ```bash
   .circleci/scripts/publish-orbs-local.sh
   ```

3. The script will:
   - Create the `posey` namespace if it doesn't exist
   - Create and publish the `common` orb first (version 0.1.0)
   - Create and publish all service orbs (version 0.1.0)
   - Create and publish all data orbs (version 0.1.0)

4. After the orbs are published, switch to using the published versions:
   ```bash
   .circleci/scripts/switch-to-published-orbs.sh
   ```

   This will:
   - Make a backup of your current config with inline orbs
   - Replace it with a version that only references published orbs
   - Remove all inline orb definitions

5. The updated config will look like this:
   ```yaml
   orbs:
     # Standard orbs from the registry
     docker: circleci/docker@2.5.0
     path-filtering: circleci/path-filtering@1.0.0
     cli: circleci/circleci-cli@0.1.9
     
     # Published orbs
     common: posey/common@0.0.5
     service-auth: posey/service-auth@0.1.0
     service-cron: posey/service-cron@0.1.0
     data-postgres: posey/data-postgres@0.1.0
     data-couchbase: posey/data-couchbase@0.1.0
     data-vector-db: posey/data-vector-db@0.1.0
     service-mcp: posey/service-mcp@0.1.0
     service-supertokens: posey/service-supertokens@0.1.0
     service-voyager: posey/service-voyager@0.1.0
     service-agents: posey/service-agents@0.1.0
   ```

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

2. Run the local publish script to publish the new orb:
   ```bash
   .circleci/scripts/publish-orbs-local.sh
   ```

3. Update `.circleci/continue_config.published.yml` to include the new orb:
   ```yaml
   orbs:
     # Existing orbs...
     your-new-orb: posey/your-new-orb@0.1.0
   ```

4. Switch to the published configuration:
   ```bash
   .circleci/scripts/switch-to-published-orbs.sh
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

## Troubleshooting

### Cannot find orb 'common' looking for command named 'common/setup-common'

This error occurs when your jobs are trying to use the common orb that hasn't been published yet. First, run the local publish script:

```bash
.circleci/scripts/publish-orbs-local.sh
```

Then switch to the published orbs configuration:

```bash
.circleci/scripts/switch-to-published-orbs.sh
```

### Cannot find circleci/circleci-cli@2.0.0 in the orb registry

Make sure you're using the correct version: `circleci/circleci-cli@0.1.9`

## How It Works

The automatic publishing process works as follows:

1. When changes are pushed to the repository, CircleCI checks if any files in the `.circleci/orbs` directory have changed.
2. If orb files have changed, the `publish-orbs` workflow is triggered.
3. The workflow:
   - Creates the namespace if it doesn't exist
   - Creates each orb if it doesn't exist
   - Publishes all orbs to the registry

This ensures that the orbs in the registry are always in sync with the orbs in the repository.

## Version Bumping

You can bump the version of orbs in one of two ways:

1. **Using the CLI command**: 
   ```bash
   yarn orbs publish --patch  # For patch version
   yarn orbs publish --minor  # For minor version
   yarn orbs publish --major  # For major version
   ```

2. **Using commit messages**:
   Add one of the following tags to your commit message to automatically bump the version appropriately when pushing to main:
   - `[patch]` - Bumps the patch version (e.g., 0.0.1 → 0.0.2)
   - `[minor]` - Bumps the minor version (e.g., 0.0.1 → 0.1.0)
   - `[major]` - Bumps the major version (e.g., 0.0.1 → 1.0.0)

   Example: `git commit -m "Update auth orb configuration [minor]"`

If no tag is specified, the default is to use a patch version bump.

## Versioning Rules

CircleCI orbs follow semantic versioning, with a few additional rules:

1. **Production versions** (e.g., `0.1.0`): Immutable once published
2. **Development versions** (e.g., `dev:alpha1`): Mutable and can be updated

## Directory Structure

- `common-orb.yml`: Common components shared across other orbs
- `service-*-orb.yml`: Orbs for specific services
- `data-*-orb.yml`: Orbs for data management services 