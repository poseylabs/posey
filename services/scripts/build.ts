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
 * Push an image to the registry with retries
 */
async function pushImageWithRetry(imageName: string, maxAttempts = 3, sleepTime = 2000): Promise<void> {
  let attempts = 0;

  while (attempts < maxAttempts) {
    try {
      attempts++;
      console.log(chalk.blue(`Pushing ${imageName} (Attempt ${attempts}/${maxAttempts})...`));

      // Always ensure fresh authentication before each attempt
      console.log(chalk.blue('Refreshing DigitalOcean registry authentication...'));
      try {
        // Ensure docker config directory exists
        if (!fs.existsSync(path.join(process.env.HOME || '~', '.docker'))) {
          await runCommand('mkdir', ['-p', path.join(process.env.HOME || '~', '.docker')]);
        }

        // Ensure valid docker config file
        const dockerConfigPath = path.join(process.env.HOME || '~', '.docker/config.json');
        if (!fs.existsSync(dockerConfigPath)) {
          fs.writeFileSync(dockerConfigPath, JSON.stringify({ auths: {} }), 'utf8');
        }

        // Try to fix potential issues with the config file
        try {
          const configContent = fs.readFileSync(dockerConfigPath, 'utf8');
          const config = JSON.parse(configContent);

          // Ensure experimental is a string, not a boolean
          if (typeof config.experimental === 'boolean') {
            config.experimental = config.experimental ? 'enabled' : 'disabled';
            fs.writeFileSync(dockerConfigPath, JSON.stringify(config, null, 2), 'utf8');
          }
        } catch (e) {
          // If we can't parse the config, create a new valid one
          fs.writeFileSync(dockerConfigPath, JSON.stringify({ auths: {} }), 'utf8');
        }

        // Login to registry
        await runCommand('doctl', ['registry', 'login', '--expiry-seconds', '3600']);

        // Verify authentication status
        await execa('doctl', ['registry', 'repository', 'list']);
        console.log(chalk.green('✅ Successfully authenticated to DigitalOcean registry'));
      } catch (authError) {
        console.warn(chalk.yellow(`Authentication refresh warning: ${(authError as Error).message}`));
        console.warn(chalk.yellow(`Will attempt push anyway...`));
      }

      // Small delay after login
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Push the image
      await runCommand('docker', ['push', imageName]);
      console.log(chalk.green(`✅ Successfully pushed ${imageName}`));
      return;
    } catch (error) {
      console.error(chalk.red(`Error pushing ${imageName} (Attempt ${attempts}/${maxAttempts}):`));
      console.error(chalk.red((error as Error).message));

      if (attempts >= maxAttempts) {
        throw new Error(`Failed to push ${imageName} after ${maxAttempts} attempts: ${(error as Error).message}`);
      }

      console.log(chalk.yellow(`Retrying in ${sleepTime / 1000} seconds...`));
      await new Promise(resolve => setTimeout(resolve, sleepTime));

      // Increase sleep time for next retry
      sleepTime = Math.min(sleepTime * 2, 15000); // Max 15 seconds
    }
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
        try {
          // Try to use buildx with direct push first
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
        } catch (error: any) {
          if (error.message?.includes('unknown flag: --push') ||
            error.message?.includes('denied') ||
            error.message?.includes('unauthorized')) {
            console.log(chalk.yellow('BuildX push failed, falling back to build + separate push...'));

            // Build locally first
            await runCommand('docker', [
              'buildx', 'build',
              '--tag', tagName,
              '--file', dockerfilePath,
              '--cache-from', 'type=local,src=/tmp/.buildx-cache',
              '--cache-to', 'type=local,dest=/tmp/.buildx-cache-new,mode=max',
              '--build-arg', 'BUILDKIT_INLINE_CACHE=1',
              ...buildArgs.map(arg => ['--build-arg', arg]).flat(),
              '--load', // Load the image into Docker instead of pushing
              contextPath
            ]);

            // Then push with retry
            await pushImageWithRetry(tagName);
          } else {
            throw error;
          }
        }
      } else {
        // Build and push separately with regular docker commands
        await runCommand('docker', [
          'build',
          '--tag', tagName,
          '--file', dockerfilePath,
          ...buildArgs.map(arg => ['--build-arg', arg]).flat(),
          contextPath
        ]);

        // Push with retry mechanism
        await pushImageWithRetry(tagName);
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
            // Use retry mechanism instead of simple push
            await pushImageWithRetry(tagName);
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
              // Use retry mechanism instead of simple push
              await pushImageWithRetry(tagName);
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
              // Use retry mechanism instead of simple push
              await pushImageWithRetry(tagName);
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