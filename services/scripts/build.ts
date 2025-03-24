#!/usr/bin/env ts-node

import { execa } from 'execa';
import chalk from 'chalk';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

// List of services that need Docker images
const services = [
  'cron',
  'auth',
  'supertokens',
  'voyager',
  'mcp',
  'agents'
];

// Parse arguments
const args = process.argv;
const isLocal = args.includes('--local');
const continueOnError = args.includes('--continue-on-error');
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
    // Check if Dockerfile exists
    const dockerfilePath = path.join(serviceDir, 'Dockerfile');
    if (!fs.existsSync(dockerfilePath)) {
      console.warn(chalk.yellow(`Dockerfile not found for ${service}, skipping...`));
      return;
    }

    // Read the Dockerfile to determine if it expects to be run from the root directory
    const dockerfileContent = fs.readFileSync(dockerfilePath, 'utf8');
    const usesServicePrefix = dockerfileContent.includes(`services/${service}/`) ||
      dockerfileContent.includes(`COPY services/`);

    // Build Docker image for the service
    if (isLocal) {
      if (usesServicePrefix) {
        // If the Dockerfile expects the services prefix, run from the parent directory
        await runCommand('docker', [
          'build',
          '--tag', `posey-${service.replace('.', '-')}:latest`,
          '--file', dockerfilePath,
          '--build-arg', `POSTGRES_DSN_POSEY=${process.env.POSTGRES_DSN_POSEY || ''}`,
          '--build-arg', `POSTGRES_DSN_SUPERTOKENS=${process.env.POSTGRES_DSN_SUPERTOKENS || ''}`,
          '--build-arg', `POSTGRES_USER=${process.env.POSTGRES_USER || ''}`,
          path.resolve(rootDir, '..')  // Use parent directory as context
        ]);
      } else {
        // Otherwise run with the service directory as context
        await runCommand('docker', [
          'build',
          '--tag', `posey-${service.replace('.', '-')}:latest`,
          '--file', dockerfilePath,
          '--build-arg', `POSTGRES_DSN_POSEY=${process.env.POSTGRES_DSN_POSEY || ''}`,
          '--build-arg', `POSTGRES_DSN_SUPERTOKENS=${process.env.POSTGRES_DSN_SUPERTOKENS || ''}`,
          '--build-arg', `POSTGRES_USER=${process.env.POSTGRES_USER || ''}`,
          serviceDir
        ]);
      }
    } else {
      // For production, with proper context handling
      if (usesServicePrefix) {
        await runCommand('docker', [
          'build',
          '--tag', `registry.digitalocean.com/posey/posey-${service.replace('.', '-')}:latest`,
          '--file', dockerfilePath,
          '--build-arg', `POSTGRES_DSN_POSEY=${process.env.POSTGRES_DSN_POSEY || ''}`,
          '--build-arg', `POSTGRES_DSN_SUPERTOKENS=${process.env.POSTGRES_DSN_SUPERTOKENS || ''}`,
          '--build-arg', `POSTGRES_USER=${process.env.POSTGRES_USER || ''}`,
          path.resolve(rootDir, '..')  // Use parent directory as context
        ]);
      } else {
        await runCommand('docker', [
          'build',
          '--tag', `registry.digitalocean.com/posey/posey-${service.replace('.', '-')}:latest`,
          '--file', dockerfilePath,
          '--build-arg', `POSTGRES_DSN_POSEY=${process.env.POSTGRES_DSN_POSEY || ''}`,
          '--build-arg', `POSTGRES_DSN_SUPERTOKENS=${process.env.POSTGRES_DSN_SUPERTOKENS || ''}`,
          '--build-arg', `POSTGRES_USER=${process.env.POSTGRES_USER || ''}`,
          serviceDir
        ]);
      }

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

  let hasErrors = false;
  const failedServices: string[] = [];

  // Process specific service if provided
  const serviceArg = args.find(arg => arg.startsWith('--service='))?.split('=')[1] ||
    args[args.indexOf('--service') + 1];

  if (serviceArg && services.includes(serviceArg)) {
    console.log(chalk.blue(`Building single service: ${serviceArg}`));
    try {
      await buildService(serviceArg);
    } catch (error: any) {
      console.error(chalk.red(`Failed to build ${serviceArg}`));
      hasErrors = true;
      failedServices.push(serviceArg);
      if (!continueOnError) {
        process.exit(1);
      }
    }
  } else {
    // Build services in parallel for faster completion
    // Split into batches based on dependency relationships
    const batch1 = ['auth', 'supertokens'];
    const batch2 = ['mcp', 'voyager', 'cron', 'agents'];

    console.log(chalk.blue('Building base services in parallel...'));
    await Promise.all(batch1.map(async (service) => {
      try {
        await buildService(service);
      } catch (error: any) {
        console.error(chalk.red(`Failed to build ${service}`));
        hasErrors = true;
        failedServices.push(service);
        if (!continueOnError) {
          process.exit(1);
        }
      }
    }));

    console.log(chalk.blue('Building dependent services in parallel...'));
    await Promise.all(batch2.map(async (service) => {
      try {
        await buildService(service);
      } catch (error: any) {
        console.error(chalk.red(`Failed to build ${service}`));
        hasErrors = true;
        failedServices.push(service);
        if (!continueOnError) {
          process.exit(1);
        }
      }
    }));
  }

  if (hasErrors) {
    console.error(chalk.red(`⚠️ Build completed with errors in the following services: ${failedServices.join(', ')}`));
    process.exit(1);
  } else {
    console.log(chalk.green('✅ All services built successfully!'));
  }
}

// Start the build process if this is the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  build();
}

// Export functions for use in other scripts
export { build, buildService }; 