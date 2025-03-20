#!/usr/bin/env ts-node

import * as execa from 'execa';
import chalk from 'chalk';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

/**
 * Executes a command with proper logging
 */
async function runCommand(command: string, args: string[] = [], options = {}): Promise<any> {
  const cmdString = `${command} ${args.join(' ')}`;
  console.log(chalk.blue(`Running: ${cmdString}`));

  try {
    const result = await execa.execa(command, args, {
      stdio: 'inherit',
      ...options
    });
    return result;
  } catch (error: any) {
    console.error(chalk.red(`Error running ${cmdString}:`));
    console.error(chalk.red(error.message));
    // Don't throw errors on cleanup - just log and continue
    return null;
  }
}

/**
 * Main function to clean resources
 */
async function clean(): Promise<void> {
  console.log(chalk.yellow('🧹 Cleaning up existing Posey data services...'));

  try {
    // Check if the namespace exists
    try {
      await execa.execa('kubectl', ['get', 'namespace', 'posey'], { stdio: 'pipe' });

      // Delete all deployments, statefulsets, pods and services
      console.log(chalk.yellow('Deleting existing deployments, statefulsets and services...'));
      await runCommand('kubectl', ['delete', 'deployments,statefulsets,pods,services', '--all', '-n', 'posey']);

      // Wait a bit for resources to be cleaned up
      console.log(chalk.yellow('Waiting for resources to terminate...'));
      await new Promise(resolve => setTimeout(resolve, 5000));

      // Check if any pods are still terminating
      const { stdout } = await execa.execa('kubectl', ['get', 'pods', '-n', 'posey', '-o', 'json'], { stdio: 'pipe' });
      const pods = JSON.parse(stdout);

      if (pods.items && pods.items.length > 0) {
        console.log(chalk.yellow(`${pods.items.length} pods still terminating, waiting longer...`));
        await new Promise(resolve => setTimeout(resolve, 10000));
      }

      console.log(chalk.green('✅ Cleanup complete!'));
    } catch (error) {
      console.log(chalk.yellow('The posey namespace does not exist yet, no cleanup needed.'));
    }
  } catch (error: any) {
    console.error(chalk.red('Error during cleanup:'));
    console.error(chalk.red(error.message));
  }
}

// Export the clean function for use in other scripts
export { clean };

// If run directly, execute the clean function
if (import.meta.url === `file://${process.argv[1]}`) {
  clean().then(() => process.exit(0)).catch(() => process.exit(1));
} 