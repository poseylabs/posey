#!/usr/bin/env node

import { execa } from 'execa';
import chalk from 'chalk';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import * as dotenv from 'dotenv';
import { build } from './build';

// Load environment variables from .env file at the beginning
const envPath = path.resolve(process.cwd(), '.env');
if (fs.existsSync(envPath)) {
  console.log(chalk.blue(`Loading environment variables from ${envPath}`));
  dotenv.config({ path: envPath });
} else {
  console.warn(chalk.yellow(`No .env file found at ${envPath}, using defaults`));
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

const services = [
  'cron',
  'auth',
  'supertokens',
  'voyager',
  'mcp',
  'agents'
];

// Parse arguments
const args = process.argv.slice(2);
const useIngress = args.includes('--ingress');
const forceClean = args.includes('--clean'); // Only clean when explicitly requested
const skipClean = !forceClean; // Default to skipping cleanup
const buildOnly = args.includes('--build-only');

// Service port mappings for port forwarding
const servicePorts: Record<string, number> = {
  'supertokens': 3567,
  'mcp': 8080,
  'auth': 9000,
  'voyager': 9001,
  'agents': 9002
};

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
 * Cleans up existing resources
 */
async function clean(): Promise<void> {
  if (skipClean) {
    console.log(chalk.yellow('Skipping cleanup as requested'));
    return;
  }

  console.log(chalk.yellow('🧹 Cleaning up existing services...'));
  try {
    await runCommand('kubectl', [
      'delete',
      '-k', 'shared/k8s',
      '--ignore-not-found'
    ]);

    await runCommand('kubectl', [
      'delete',
      'deployment,statefulset,pod,service',
      '-l', 'part-of=posey-platform',
      '-n', 'posey',
      '--force',
      '--grace-period=0',
      '--ignore-not-found'
    ]);

    console.log(chalk.green('✅ Clean up completed'));
  } catch (error: any) {
    console.error(chalk.red('⚠️ Clean up failed - continuing anyway...'));
  }
}

/**
 * Create a port forwarding script for the user to run
 */
async function createPortForwardScript(): Promise<void> {
  const scriptPath = path.join(rootDir, 'port-forward.sh');

  // Create a port-forward script that the user can run manually
  let scriptContent = `#!/bin/bash\n\n`;
  scriptContent += `# Port forwarding script for Posey Services\n`;
  scriptContent += `# Run this script to forward local ports to Kubernetes services\n\n`;

  Object.entries(servicePorts).forEach(([service, port]) => {
    scriptContent += `echo "Setting up port forwarding for ${service} on localhost:${port}"\n`;
    scriptContent += `kubectl port-forward svc/${service} ${port}:${port} -n posey &\n\n`;
  });

  scriptContent += `echo "Port forwarding is running in the background. Press CTRL+C to stop all port forwards."\n`;
  scriptContent += `echo "Services are now accessible at:"\n`;
  Object.entries(servicePorts).forEach(([service, port]) => {
    scriptContent += `echo "  - ${service}: http://localhost:${port}"\n`;
  });
  scriptContent += `\n`;
  scriptContent += `# Wait for user to press CTRL+C\n`;
  scriptContent += `read -p "Press CTRL+C to stop port forwarding..."\n`;
  scriptContent += `# Kill all port-forward processes\n`;
  scriptContent += `pkill -f "kubectl port-forward"\n`;
  scriptContent += `echo "All port forwarding stopped"\n`;

  try {
    fs.writeFileSync(scriptPath, scriptContent);
    fs.chmodSync(scriptPath, '755'); // Make the script executable
    console.log(chalk.green(`\n✅ Created port forwarding script at: ${scriptPath}`));
    console.log(chalk.cyan(`Run it with: ${scriptPath}`));
    console.log(chalk.cyan(`Or: cd ${rootDir} && ./port-forward.sh`));
  } catch (error: any) {
    console.error(chalk.red(`Failed to create port forwarding script: ${error.message}`));
  }
}

/**
 * Deploy a single service
 */
async function deployService(service: string): Promise<void> {
  console.log(chalk.cyan(`Deploying service: ${service}`));

  const serviceDir = path.join(rootDir, service);
  const k8sDir = path.join(serviceDir, 'k8s');

  if (!fs.existsSync(k8sDir)) {
    console.log(chalk.yellow(`No k8s directory found for ${service}, skipping`));
    return;
  }

  // Find all yaml files in the k8s directory
  let files = fs.readdirSync(k8sDir)
    .filter(file => file.endsWith('.yaml'))
    .sort();

  // Handle PVC files first and separately
  const pvcFiles = files.filter(file => file.includes('pvc') || file.includes('persistentvolume'));
  const nonPvcFiles = files.filter(file => !pvcFiles.includes(file));

  // Apply PVC files if they don't already exist
  for (const file of pvcFiles) {
    const filePath = path.join(k8sDir, file);
    console.log(chalk.blue(`Checking PVC file: ${filePath}`));

    try {
      // Read the YAML file to get PVC name
      const yamlContent = fs.readFileSync(filePath, 'utf8');
      const pvcMatch = yamlContent.match(/name:\s*([a-zA-Z0-9-]+)/);

      if (pvcMatch && pvcMatch[1]) {
        const pvcName = pvcMatch[1];

        // Check if PVC already exists
        try {
          await execa('kubectl', ['get', 'pvc', pvcName, '-n', 'posey', '--no-headers']);
          console.log(chalk.yellow(`⚠️ PVC ${pvcName} already exists, skipping creation to avoid resize issues`));
        } catch (error) {
          // PVC doesn't exist, create it
          console.log(chalk.blue(`Creating PVC: ${pvcName}`));
          await runCommand('kubectl', ['apply', '-f', filePath, '-n', 'posey']);
        }
      } else {
        // Couldn't parse PVC name, try applying anyway
        console.log(chalk.yellow(`⚠️ Couldn't determine PVC name from ${file}, applying directly`));
        await runCommand('kubectl', ['apply', '-f', filePath, '-n', 'posey']);
      }
    } catch (error: any) {
      console.warn(chalk.yellow(`⚠️ PVC deployment failed, but continuing: ${error.message}`));
    }
  }

  // Apply non-PVC files
  for (const file of nonPvcFiles) {
    const filePath = path.join(k8sDir, file);
    console.log(chalk.blue(`Applying ${filePath}`));

    try {
      await runCommand('kubectl', ['apply', '-f', filePath, '-n', 'posey']);
    } catch (error: any) {
      // Handle all kinds of "already exists" errors
      if (error.message &&
        (error.message.includes('AlreadyExists') ||
          error.message.includes('already exists'))) {
        console.warn(chalk.yellow(`⚠️ Resource in ${filePath} already exists, continuing`));
      } else {
        console.error(chalk.red(`Failed to apply ${filePath}:`));
        console.error(chalk.red(error.message));
        throw error;
      }
    }
  }
}

/**
 * Main function to start the development environment
 */
async function dev(): Promise<void> {
  console.log(chalk.green('🚀 Starting Posey Services Development Environment'));

  try {
    // First, clean up any existing resources if specifically requested
    if (skipClean) {
      console.log(chalk.yellow('ℹ️ Cleanup is skipped by default to protect data services.'));
      console.log(chalk.yellow('To force cleanup, use --clean flag instead of --skip-clean.'));
    } else {
      console.log(chalk.red('⚠️ WARNING: Performing cleanup. This may delete data services!'));
      await clean();
    }

    // Setup environment variables
    console.log(chalk.yellow('Setting up environment variables...'));
    try {
      // Use the correct absolute path to the script with proper parameters
      await runCommand('bash', [
        path.resolve(rootDir, '../scripts/k8s-env-setup.sh'),
        'posey',
        '',  // Empty string for APP_NAME parameter
        path.resolve(rootDir)
      ]);
      console.log(chalk.green('✅ Environment setup completed'));
    } catch (error: any) {
      console.warn(chalk.yellow('⚠️ Some environment setup steps failed, but continuing deployment...'));
      // Continue without failing to allow deployment to proceed
    }

    // Build Docker images for all services
    console.log(chalk.yellow('Building Docker images for all services...'));
    try {
      // Force continue-on-error for dev environments
      process.argv.push('--continue-on-error');
      await build();
      console.log(chalk.green('✅ All Docker images built successfully'));

      if (buildOnly) {
        console.log(chalk.yellow('Build completed. Skipping deployment as requested with --build-only'));
        process.exit(0);
      }
    } catch (error: any) {
      console.error(chalk.red('⚠️ Failed to build some Docker images:'));
      console.error(chalk.red(error.message));

      if (buildOnly) {
        console.error(chalk.red('Build failed and --build-only was specified. Exiting.'));
        process.exit(1);
      }

      console.log(chalk.yellow('Continuing with deployment anyway...'));
    }

    // Apply shared resources
    console.log(chalk.yellow('Applying shared Kubernetes resources...'));
    await runCommand('kubectl', ['apply', '-k', 'shared/k8s', '-n', 'posey']);

    // Deploy services
    for (const service of services) {
      await deployService(service);
    }

    // Setup ingress if requested
    if (useIngress) {
      console.log(chalk.yellow('Setting up local ingress...'));
      try {
        // Use our dedicated script to apply ingress resources
        console.log(chalk.blue('Running apply-ingress script to set up ingress resources...'));
        await runCommand('node', [
          '--loader', 'ts-node/esm',
          path.join(rootDir, 'shared/scripts', 'apply-ingress.ts')
        ]);

        console.log(chalk.green('✅ Ingress set up successfully!'));
        console.log(chalk.yellow('\nService Connection Details:'));
        console.log(chalk.cyan('Supertokens: http://localhost:3567'));
        console.log(chalk.cyan('MCP: http://localhost:8080'));
        console.log(chalk.cyan('Agents: https://agents.local.posey.ai'));
        console.log(chalk.cyan('Auth: https://auth.local.posey.ai'));
        console.log(chalk.cyan('Cron: https://cron.local.posey.ai'));
        console.log(chalk.cyan('Voyager: https://voyager.local.posey.ai'));
      } catch (error: any) {
        console.error(chalk.red('Failed to set up ingress:'));
        console.error(chalk.red(error.message));
        console.log(chalk.yellow('Continuing with standard services...'));
      }
    }

    // Set up port forwarding for local development
    await createPortForwardScript();

    console.log(chalk.green('✅ All services are running!'));
    console.log(chalk.cyan('Available services:'));

    services.forEach(service => {
      console.log(chalk.cyan(`  - ${service}`));
    });

    // Display service details
    await runCommand('kubectl', ['get', 'services', '-n', 'posey']);

    console.log(chalk.yellow('\nTo stop the services, run: kubectl delete -n posey deployment,service --all'));

    // Exit successfully
    process.exit(0);
  } catch (error: any) {
    console.error(chalk.red('Failed to start development environment:'));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

// Start the development environment
if (import.meta.url === `file://${process.argv[1]}`) {
  dev();
} 