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

    // Common build arguments
    const buildArgs = [
      `POSTGRES_DSN_POSEY=${process.env.POSTGRES_DSN_POSEY || ''}`,
      `POSTGRES_DSN_SUPERTOKENS=${process.env.POSTGRES_DSN_SUPERTOKENS || ''}`,
      `POSTGRES_USER=${process.env.POSTGRES_USER || ''}`
    ];

    // Check if buildx is available with advanced features
    let hasBuildxAdvancedFeatures = false;
    try {
      const buildxResult = await execa('docker', ['buildx', 'version']);
      // Check if buildx version is at least v0.8 which supports cache mounts
      const versionMatch = buildxResult.stdout.match(/v(\d+)\.(\d+)/);
      if (versionMatch && (parseInt(versionMatch[1]) > 0 || parseInt(versionMatch[2]) >= 8)) {
        hasBuildxAdvancedFeatures = true;
      }
    } catch (error) {
      console.log(chalk.yellow('Docker buildx with advanced features not available, using standard build'));
    }

    // Determine the context path
    const contextPath = usesServicePrefix ? path.resolve(rootDir, '..') : serviceDir;

    // Build Docker image for the service
    if (isLocal) {
      const tagName = `posey-${service.replace('.', '-')}:latest`;

      if (hasBuildxAdvancedFeatures) {
        // Use buildx with advanced features
        await runCommand('docker', [
          'buildx', 'build',
          '--tag', tagName,
          '--file', dockerfilePath,
          '--cache-from', 'type=local,src=/tmp/.buildx-cache',
          '--cache-to', 'type=local,dest=/tmp/.buildx-cache-new,mode=max',
          '--build-arg', 'BUILDKIT_INLINE_CACHE=1',
          ...buildArgs.map(arg => ['--build-arg', arg]).flat(),
          '--load', // Load the image into Docker
          contextPath
        ]);
      } else {
        // Fall back to regular docker build
        await runCommand('docker', [
          'build',
          '--tag', tagName,
          '--file', dockerfilePath,
          ...buildArgs.map(arg => ['--build-arg', arg]).flat(),
          contextPath
        ]);
      }
    } else {
      // For production
      const tagName = `registry.digitalocean.com/posey/posey-${service.replace('.', '-')}:latest`;

      if (hasBuildxAdvancedFeatures) {
        // Use buildx with advanced features for production
        await runCommand('docker', [
          'buildx', 'build',
          '--tag', tagName,
          '--file', dockerfilePath,
          '--cache-from', 'type=local,src=/tmp/.buildx-cache',
          '--cache-to', 'type=local,dest=/tmp/.buildx-cache-new,mode=max',
          '--build-arg', 'BUILDKIT_INLINE_CACHE=1',
          ...buildArgs.map(arg => ['--build-arg', arg]).flat(),
          '--push', // Push directly to registry
          contextPath
        ]);
      } else {
        // Build and push separately with regular docker commands
        await runCommand('docker', [
          'build',
          '--tag', tagName,
          '--file', dockerfilePath,
          ...buildArgs.map(arg => ['--build-arg', arg]).flat(),
          contextPath
        ]);

        // Push after building
        await runCommand('docker', [
          'push',
          tagName
        ]);
      }
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

  // Verify Docker and Buildx installation
  try {
    console.log(chalk.blue('Verifying Docker installation...'));
    await runCommand('docker', ['--version']);

    console.log(chalk.blue('Checking Buildx availability...'));
    try {
      await runCommand('docker', ['buildx', 'version']);
      console.log(chalk.green('✅ Docker Buildx is available'));
    } catch (error) {
      console.log(chalk.yellow('⚠️ Docker Buildx not available or has limited functionality'));
      console.log(chalk.yellow('Will use standard Docker build commands as fallback'));
    }
  } catch (error) {
    console.error(chalk.red('❌ Docker verification failed. Please ensure Docker is installed.'));
    process.exit(1);
  }

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
      console.error(chalk.red(error.message));

      // Attempt a fallback build with basic Docker commands if advanced features fail
      if (error.message?.includes('unknown flag') || error.message?.includes('buildx')) {
        console.log(chalk.yellow(`Attempting fallback build for ${serviceArg} with basic Docker...`));
        try {
          const serviceDir = path.join(rootDir, serviceArg);
          const dockerfilePath = path.join(serviceDir, 'Dockerfile');
          const contextPath = fs.readFileSync(dockerfilePath, 'utf8').includes(`services/${serviceArg}/`)
            ? path.resolve(rootDir, '..')
            : serviceDir;

          const tagName = isLocal
            ? `posey-${serviceArg.replace('.', '-')}:latest`
            : `registry.digitalocean.com/posey/posey-${serviceArg.replace('.', '-')}:latest`;

          await runCommand('docker', [
            'build',
            '--tag', tagName,
            '--file', dockerfilePath,
            contextPath
          ]);

          if (!isLocal) {
            await runCommand('docker', ['push', tagName]);
          }

          console.log(chalk.green(`✅ Successfully built ${serviceArg} using fallback method`));
          return;
        } catch (fallbackError: any) {
          console.error(chalk.red(`Fallback build also failed for ${serviceArg}:`));
          console.error(chalk.red(fallbackError.message));
        }
      }

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
        console.error(chalk.red(error.message));

        // Attempt fallback build
        if (error.message?.includes('unknown flag') || error.message?.includes('buildx')) {
          console.log(chalk.yellow(`Attempting fallback build for ${service} with basic Docker...`));
          try {
            const serviceDir = path.join(rootDir, service);
            const dockerfilePath = path.join(serviceDir, 'Dockerfile');
            if (!fs.existsSync(dockerfilePath)) {
              console.warn(chalk.yellow(`Dockerfile not found for ${service}, skipping...`));
              return;
            }

            const contextPath = fs.readFileSync(dockerfilePath, 'utf8').includes(`services/${service}/`)
              ? path.resolve(rootDir, '..')
              : serviceDir;

            const tagName = isLocal
              ? `posey-${service.replace('.', '-')}:latest`
              : `registry.digitalocean.com/posey/posey-${service.replace('.', '-')}:latest`;

            await runCommand('docker', [
              'build',
              '--tag', tagName,
              '--file', dockerfilePath,
              contextPath
            ]);

            if (!isLocal) {
              await runCommand('docker', ['push', tagName]);
            }

            console.log(chalk.green(`✅ Successfully built ${service} using fallback method`));
            return;
          } catch (fallbackError: any) {
            console.error(chalk.red(`Fallback build also failed for ${service}:`));
            console.error(chalk.red(fallbackError.message));
          }
        }

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
        console.error(chalk.red(error.message));

        // Attempt fallback build
        if (error.message?.includes('unknown flag') || error.message?.includes('buildx')) {
          console.log(chalk.yellow(`Attempting fallback build for ${service} with basic Docker...`));
          try {
            const serviceDir = path.join(rootDir, service);
            const dockerfilePath = path.join(serviceDir, 'Dockerfile');
            if (!fs.existsSync(dockerfilePath)) {
              console.warn(chalk.yellow(`Dockerfile not found for ${service}, skipping...`));
              return;
            }

            const contextPath = fs.readFileSync(dockerfilePath, 'utf8').includes(`services/${service}/`)
              ? path.resolve(rootDir, '..')
              : serviceDir;

            const tagName = isLocal
              ? `posey-${service.replace('.', '-')}:latest`
              : `registry.digitalocean.com/posey/posey-${service.replace('.', '-')}:latest`;

            await runCommand('docker', [
              'build',
              '--tag', tagName,
              '--file', dockerfilePath,
              contextPath
            ]);

            if (!isLocal) {
              await runCommand('docker', ['push', tagName]);
            }

            console.log(chalk.green(`✅ Successfully built ${service} using fallback method`));
            return;
          } catch (fallbackError: any) {
            console.error(chalk.red(`Fallback build also failed for ${service}:`));
            console.error(chalk.red(fallbackError.message));
          }
        }

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