#!/usr/bin/env ts-node

import * as execa from 'execa';
import chalk from 'chalk';

/**
 * Clean up only non-running init containers without affecting running services
 */
async function cleanupInitContainers(): Promise<void> {
  console.log(chalk.green('\n🧹 Cleaning up non-running init containers...\n'));

  try {
    // Find all non-running init containers
    console.log(chalk.blue('Finding non-running init containers...'));

    const exitedContainers = await execa.execa('docker',
      ['ps', '-a', '--filter', 'status=exited', '--filter', 'name=k8s_init', '--format', '{{.ID}} {{.Names}} {{.Status}}'],
      { stdio: 'pipe' }
    );

    if (!exitedContainers.stdout) {
      console.log(chalk.green('No non-running init containers found.'));
      return;
    }

    const containerInfo = exitedContainers.stdout.split('\n').filter(Boolean);

    if (containerInfo.length === 0) {
      console.log(chalk.green('No non-running init containers found.'));
      return;
    }

    console.log(chalk.blue(`Found ${containerInfo.length} non-running init containers to clean up:`));

    // Display information about containers to be removed
    for (const info of containerInfo) {
      console.log(chalk.blue(`  ${info}`));
    }

    console.log(chalk.yellow('\nRemoving non-running init containers...'));

    // Remove all exited init containers
    let removed = 0;
    for (const info of containerInfo) {
      const containerId = info.split(' ')[0];
      try {
        await execa.execa('docker', ['rm', containerId], { stdio: 'inherit' });
        removed++;
      } catch (err: any) {
        console.log(chalk.red(`Failed to remove container ${containerId}: ${err.message}`));
      }
    }

    console.log(chalk.green(`\n✅ Cleanup completed. Removed ${removed} non-running init containers.`));
  } catch (error: any) {
    console.error(chalk.red(`Container cleanup encountered issues: ${error.message}`));
    process.exit(1);
  }
}

// Run the cleanup
cleanupInitContainers(); 