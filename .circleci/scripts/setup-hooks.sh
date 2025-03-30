#!/bin/bash
# Script to set up git hooks for the project

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.circleci/hooks"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

# Check if the hooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
  echo "Hooks directory not found: $HOOKS_DIR"
  exit 1
fi

# Install pre-push hook
if [ -f "$HOOKS_DIR/pre-push" ]; then
  echo "Installing pre-push hook..."
  cp "$HOOKS_DIR/pre-push" "$GIT_HOOKS_DIR/pre-push"
  chmod +x "$GIT_HOOKS_DIR/pre-push"
  echo "pre-push hook installed successfully"
else
  echo "pre-push hook not found: $HOOKS_DIR/pre-push"
fi

echo "Git hooks setup complete!" 