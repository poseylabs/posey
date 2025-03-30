#!/bin/bash
set -e

# This script switches the continue_config.yml to use published orbs instead of inline orbs

# Backup the current config
cp .circleci/continue_config.yml .circleci/continue_config.inline.yml

# Copy the published orbs version which only uses published orb references
# and doesn't include any inline orb definitions
cp .circleci/continue_config.published.yml .circleci/continue_config.yml

echo "Switched to published orbs configuration."
echo "The original inline orbs config has been backed up to .circleci/continue_config.inline.yml"
echo ""
echo "The inline orb definitions have been completely removed from the active configuration."
echo "Make sure you have run .circleci/scripts/publish-orbs-local.sh before pushing to CircleCI"
echo "or your builds will fail with 'Cannot find orb' errors." 