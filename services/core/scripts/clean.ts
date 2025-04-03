#!/usr/bin/env node

import { execa } from 'execa';
import chalk from 'chalk';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

// List of services we manage in our deployment
const services = [
  'cron',
  'auth',
  'supertokens',
  'voyager',
  'mcp',
  'agents'
];

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
 * Cleans up Kubernetes resources for our services
 */
async function clean(): Promise<void> {
  console.log(chalk.yellow('🧹 Cleaning up all service resources...'));

  try {
    // Delete network policies and other shared resources
    console.log(chalk.yellow('Deleting shared resources...'));
    await runCommand('kubectl', ['delete', 'networkpolicy', '-n', 'posey', '-l', 'app.kubernetes.io/part-of=posey-services', '--ignore-not-found']);

    // Delete each service individually rather than deleting all labeled resources
    for (const service of services) {
      console.log(chalk.yellow(`Cleaning up resources for service: ${service}`));

      // Delete deployments for this service
      await runCommand('kubectl', [
        'delete',
        'deployment',
        `-l`, `app.kubernetes.io/name=posey-${service}`,
        '-n', 'posey',
        '--force',
        '--grace-period=0',
        '--ignore-not-found'
      ]);

      // Delete services for this service
      await runCommand('kubectl', [
        'delete',
        'service',
        `posey-${service}`,
        '-n', 'posey',
        '--ignore-not-found'
      ]);

      // Delete ingress for this service if it exists
      await runCommand('kubectl', [
        'delete',
        'ingress',
        `${service}-ingress`,
        '-n', 'posey',
        '--ignore-not-found'
      ]);
    }

    console.log(chalk.green('✅ Clean up completed successfully!'));
  } catch (error: any) {
    console.error(chalk.red('Failed to clean up resources:'));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  clean();
} 