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

      // Use labels to specifically target only data services
      // The key is to use labels that distinguish data services from platform services
      console.log(chalk.yellow('Deleting only data services (postgres, qdrant, couchbase)...'));

      // Define the data services we manage
      const dataServices = ['postgres', 'qdrant', 'couchbase'];

      for (const service of dataServices) {
        console.log(chalk.yellow(`Cleaning up resources for data service: ${service}`));

        // Delete deployments and statefulsets for this data service
        await runCommand('kubectl', [
          'delete',
          'deployment,statefulset',
          `posey-${service}`,
          '-n', 'posey',
          '--ignore-not-found'
        ]);

        // Delete services for this data service
        await runCommand('kubectl', [
          'delete',
          'service',
          `posey-${service}`,
          '-n', 'posey',
          '--ignore-not-found'
        ]);
      }

      // Wait a bit for resources to be cleaned up
      console.log(chalk.yellow('Waiting for resources to terminate...'));
      await new Promise(resolve => setTimeout(resolve, 5000));

      // Check if any pods for data services are still terminating
      const { stdout } = await execa.execa('kubectl', [
        'get', 'pods',
        '-n', 'posey',
        '-l', 'component in (postgres,qdrant,couchbase)',
        '-o', 'json'
      ], { stdio: 'pipe' });

      const pods = JSON.parse(stdout);

      if (pods.items && pods.items.length > 0) {
        console.log(chalk.yellow(`${pods.items.length} pods still terminating, waiting longer...`));
        await new Promise(resolve => setTimeout(resolve, 10000));
      }

      console.log(chalk.green('✅ Cleanup complete!'));
      console.log(chalk.yellow('⚠️ Note: Platform services (cron, auth, supertokens, voyager, mcp, agents) were preserved.'));
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