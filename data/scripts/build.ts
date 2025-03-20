#!/usr/bin/env ts-node

import * as execa from 'execa';
import chalk from 'chalk';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

const services = [
  'postgres',
  'couchbase',
  'vector.db',
  'graphql'
];

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
    const result = await execa.execa(command, args, {
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
 * Build a specific service
 */
async function buildService(service: string): Promise<void> {
  const serviceDir = path.join(rootDir, service);

  if (!fs.existsSync(serviceDir)) {
    console.warn(chalk.yellow(`Service directory ${service} not found, skipping...`));
    return;
  }

  console.log(chalk.green(`\n📦 Building ${service} for ${environment}...\n`));

  try {
    // Build Docker image for the service
    if (isLocal) {
      await runCommand('docker', [
        'build',
        '--tag', `posey-${service.replace('.', '-')}:latest`,
        '--file', path.join(serviceDir, 'Dockerfile'),
        serviceDir
      ]);
    } else {
      // For production, we would tag with the registry
      await runCommand('docker', [
        'build',
        '--tag', `registry.digitalocean.com/posey/posey-${service.replace('.', '-')}:latest`,
        '--file', path.join(serviceDir, 'Dockerfile'),
        serviceDir
      ]);

      // Push to registry for production
      await runCommand('docker', [
        'push',
        `registry.digitalocean.com/posey/posey-${service.replace('.', '-')}:latest`
      ]);
    }

    console.log(chalk.green(`✅ Successfully built ${service} for ${environment}`));
  } catch (error: any) {
    console.error(chalk.red(`Failed to build ${service}:`));
    console.error(chalk.red(error.message));
    throw error;
  }
}

/**
 * Main build function
 */
async function build(): Promise<void> {
  console.log(chalk.green(`🔨 Building all services for ${environment}...\n`));

  try {
    for (const service of services) {
      await buildService(service);
    }

    console.log(chalk.green(`\n✅ All services built successfully for ${environment}`));
  } catch (error: any) {
    console.error(chalk.red('\nBuild process failed:'));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

// Start the build process
build(); 