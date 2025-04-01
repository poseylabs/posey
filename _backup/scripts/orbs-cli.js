#!/usr/bin/env node

/**
 * Orbs CLI - A wrapper for CircleCI orb commands with npm-style arguments
 * 
 * Usage:
 *   yarn orbs version          - Show all orb versions
 *   yarn orbs publish --patch  - Publish with patch bump
 *   yarn orbs publish --minor  - Publish with minor bump
 *   yarn orbs publish --major  - Publish with major bump
 *   yarn orbs switch           - Switch to published orbs
 */

import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

// Ensure CIRCLE_TOKEN is set if available in .env
function ensureCircleToken() {
  // Skip if CIRCLE_TOKEN is already set
  if (process.env.CIRCLE_TOKEN) {
    return;
  }

  const envPath = path.join(rootDir, '.env');
  if (fs.existsSync(envPath)) {
    try {
      const envContent = fs.readFileSync(envPath, 'utf8');
      const match = envContent.match(/CIRCLECI_API_TOKEN=(.*)/);
      if (match && match[1]) {
        process.env.CIRCLE_TOKEN = match[1].trim();
        console.log('Using CircleCI token from .env file');
      }
    } catch (error) {
      console.warn('Warning: Could not read .env file');
    }
  }
}

// Get command line arguments
const args = process.argv.slice(2);
const command = args[0] || 'help';

function executeCommand(cmd) {
  try {
    ensureCircleToken(); // Make sure CIRCLE_TOKEN is set
    return execSync(cmd, {
      stdio: 'inherit',
      cwd: rootDir,
      env: { ...process.env }  // Pass all env vars including our CIRCLE_TOKEN
    });
  } catch (error) {
    console.error(`Error executing command: ${cmd}`);
    process.exit(1);
  }
}

function showHelp() {
  console.log(`
Orbs CLI - A wrapper for CircleCI orb commands with npm-style arguments

Commands:
  yarn orbs version          - Show all orb versions
  yarn orbs publish --patch  - Publish with patch bump
  yarn orbs publish --minor  - Publish with minor bump
  yarn orbs publish --major  - Publish with major bump
  yarn orbs switch           - Switch to published orbs
  `);
}

// Handle different commands
switch (command) {
  case 'version':
    executeCommand('bash .circleci/scripts/orb-versions.sh');
    break;

  case 'publish':
    // Parse npm-style arguments
    if (args.includes('--patch')) {
      executeCommand('bash .circleci/scripts/publish-orbs-local.sh patch');
    } else if (args.includes('--minor')) {
      executeCommand('bash .circleci/scripts/publish-orbs-local.sh minor');
    } else if (args.includes('--major')) {
      executeCommand('bash .circleci/scripts/publish-orbs-local.sh major');
    } else {
      // Default to patch if no specific version bump is provided
      executeCommand('bash .circleci/scripts/publish-orbs-local.sh patch');
    }
    break;

  case 'switch':
    executeCommand('bash .circleci/scripts/switch-to-published-orbs.sh');
    break;

  case 'help':
  default:
    showHelp();
    break;
} 