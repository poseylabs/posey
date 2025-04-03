#!/usr/bin/env node

import { execa } from 'execa';
import chalk from 'chalk';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import * as dotenv from 'dotenv';

// Load environment variables from .env file
const envPath = path.resolve(process.cwd(), '.env');
if (fs.existsSync(envPath)) {
  console.log(chalk.blue(`Loading environment variables from ${envPath}`));
  dotenv.config({ path: envPath });
} else {
  console.warn(chalk.yellow(`No .env file found at ${envPath}, using defaults`));
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

// Parse command line arguments
const args = process.argv.slice(2);
const isLocal = args.includes('--local');
const skipDeploy = args.includes('--skip-deploy');
const namespace = 'posey'; // Default namespace

// Service list
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

  // Filter files based on environment (local vs production)
  if (isLocal) {
    // For local deployment, prefer -local.yaml files when they exist
    const localFiles = files.filter(file => file.includes('-local.yaml'));
    const nonLocalFiles = files.filter(file => !file.includes('-local.yaml'));

    // Create a map to track which base files have local versions
    const fileMap = new Map();

    for (const file of localFiles) {
      const baseName = file.replace('-local.yaml', '.yaml');
      fileMap.set(baseName, file);
    }

    // Use local versions when available, otherwise use the base version
    files = nonLocalFiles.filter(file => !fileMap.has(file)).concat(Array.from(fileMap.values()));

    console.log(chalk.blue(`Using local deployment files for ${service}: ${files.join(', ')}`));
  } else {
    // For production deployment, exclude -local.yaml files
    files = files.filter(file => !file.includes('-local.yaml'));
    console.log(chalk.blue(`Using production deployment files for ${service}: ${files.join(', ')}`));
  }

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
          await execa('kubectl', ['get', 'pvc', pvcName, '-n', namespace, '--no-headers']);
          console.log(chalk.yellow(`⚠️ PVC ${pvcName} already exists, skipping creation to avoid resize issues`));
        } catch (error) {
          // PVC doesn't exist, create it
          console.log(chalk.blue(`Creating PVC: ${pvcName}`));
          await runCommand('kubectl', ['apply', '-f', filePath, '-n', namespace]);
        }
      } else {
        // Couldn't parse PVC name, try applying anyway
        console.log(chalk.yellow(`⚠️ Couldn't determine PVC name from ${file}, applying directly`));
        await runCommand('kubectl', ['apply', '-f', filePath, '-n', namespace]);
      }
    } catch (error) {
      console.warn(chalk.yellow(`⚠️ PVC deployment failed, but continuing: ${error.message}`));
    }
  }

  // Apply non-PVC files
  for (const file of nonPvcFiles) {
    const filePath = path.join(k8sDir, file);
    console.log(chalk.blue(`Applying ${filePath}`));

    try {
      await runCommand('kubectl', ['apply', '-f', filePath, '-n', namespace]);
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
 * Main deployment function
 */
async function deploy(): Promise<void> {
  const deployTarget = isLocal ? 'local' : 'production';
  console.log(chalk.green(`🚀 Deploying Posey Services to ${deployTarget} environment (namespace: ${namespace})`));

  try {
    // Setup environment variables
    console.log(chalk.yellow('Setting up environment variables...'));
    try {
      // Use the correct absolute path to the script with proper parameters
      await runCommand('bash', [
        path.resolve(rootDir, '../scripts/k8s-env-setup.sh'),
        namespace,
        '',  // Empty string for APP_NAME parameter
        path.resolve(rootDir)
      ]);
      console.log(chalk.green('✅ Environment setup completed'));
    } catch (error: any) {
      console.warn(chalk.yellow('⚠️ Some environment setup steps failed, but continuing deployment...'));
      // Continue without failing to allow deployment to proceed
    }

    // Apply shared resources
    console.log(chalk.yellow('Applying shared Kubernetes resources...'));
    await runCommand('kubectl', ['apply', '-k', 'shared/k8s', '-n', namespace]);

    if (skipDeploy) {
      console.log(chalk.yellow('Skipping deployment as requested'));
      process.exit(0);
      return;
    }

    // Deploy each service
    for (const service of services) {
      await deployService(service);
    }

    // Verify deployment
    console.log(chalk.blue('\nVerifying deployment...'));
    await runCommand('kubectl', ['get', 'pods', '-n', namespace]);

    console.log(chalk.green('✅ All services deployed successfully!'));
    console.log(chalk.yellow('\nTo check the status of the pods:'));
    console.log(chalk.cyan(`  kubectl get pods -n ${namespace}`));

    // Exit successfully
    process.exit(0);
  } catch (error: any) {
    console.error(chalk.red('Failed to deploy services:'));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

// Start the deployment process only if this is the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  deploy();
} 