#!/usr/bin/env ts-node

import { execa } from 'execa';
import chalk from 'chalk';
import path from 'path';
import { fileURLToPath } from 'url';
import { build } from './build';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

// Parse arguments
const isLocal = process.argv.includes('--local');
const environment = isLocal ? 'local' : 'production';

/**
 * Executes a command with proper logging
 */
async function runCommand(command: string, args: string[] = [], options = {}): Promise<any> {
  const cmdString = `${command} ${args.join(' ')}`;
  console.log(chalk.blue(`Running: ${cmdString}`));

  try {
    const result = await execa(command, args, {
      stdio: 'inherit',
      ...options
    });
    return result;
  } catch (error: any) {
    console.error(chalk.red(`Error running ${cmdString}:`));
    console.error(chalk.red(error.message));
    throw error;
  }
}

/**
 * Main function to start the production environment
 */
async function start(): Promise<void> {
  console.log(chalk.green(`🚀 Starting Posey Services ${environment.toUpperCase()} Environment`));

  try {
    // Build all services for the specified environment
    console.log(chalk.yellow(`Building ${environment} services...`));
    if (isLocal) {
      await build();
    } else {
      await build();
    }

    // Deploy all services for the specified environment
    console.log(chalk.yellow(`Deploying ${environment} services...`));
    await runCommand('node', [
      '--loader', 'ts-node/esm',
      path.join(rootDir, 'scripts', 'deploy.ts'),
      isLocal ? '--local' : ''
    ].filter(Boolean), { cwd: rootDir });

    console.log(chalk.green(`✅ All ${environment} services are running!`));

    // Display services and their status
    await runCommand('kubectl', ['get', 'pods', '-n', 'posey']);

    console.log(chalk.yellow('\nService Connection Details:'));
    console.log(chalk.cyan('Supertokens: http://supertokens.posey.ai:3567'));
    console.log(chalk.cyan('MCP: http://mcp.posey.ai:8080'));
    console.log(chalk.cyan('Agents: https://agents.posey.ai'));
    console.log(chalk.cyan('Auth: https://auth.posey.ai'));
    console.log(chalk.cyan('Cron: https://cron.posey.ai'));
    console.log(chalk.cyan('Voyager: https://voyager.posey.ai'));

    console.log(chalk.yellow('\nPress Ctrl+C to exit the monitoring'));

    // Keep monitoring the pods
    await runCommand('kubectl', ['get', 'pods', '-n', 'posey', '-w']);
  } catch (error: any) {
    console.error(chalk.red(`Failed to start ${environment} environment:`));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

// Start the production environment if this is the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  start();
}

// Export functions for use in other scripts
export { start, runCommand }; 