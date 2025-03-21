#!/usr/bin/env ts-node

import * as execa from 'execa';
import chalk from 'chalk';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

// Load environment variables from .env file
dotenv.config({ path: path.join(rootDir, '.env') });

const services = [
  'postgres',
  'couchbase',
  'vector.db',
  'graphql'
];

// Parse arguments
const isLocal = process.argv.includes('--local');
const isStaging = process.argv.includes('--staging');
const environment = isLocal ? 'local' : isStaging ? 'staging' : 'production';
const namespace = process.env.KUBE_NAMESPACE || (isStaging ? 'posey-staging' : 'posey');

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
 * Process a template file by replacing environment variables
 */
function processTemplate(filePath: string): string {
  let template = fs.readFileSync(filePath, 'utf8');

  // Replace ${VARIABLE} with actual env values
  template = template.replace(/\${([^}]+)}/g, (match, key) => {
    return process.env[key] || '';
  });

  return template;
}

/**
 * Deploy a specific service to Kubernetes
 */
async function deployService(service: string): Promise<void> {
  const serviceDir = path.join(rootDir, service);
  const k8sDir = path.join(serviceDir, 'k8s');

  if (!fs.existsSync(serviceDir)) {
    console.warn(chalk.yellow(`Service directory ${service} not found, skipping...`));
    return;
  }

  if (!fs.existsSync(k8sDir)) {
    console.warn(chalk.yellow(`K8s directory for ${service} not found, skipping...`));
    return;
  }

  console.log(chalk.green(`\n🚀 Deploying ${service} for ${environment} to namespace ${namespace}...\n`));

  try {
    // Apply ConfigMap if it exists
    const configMapPath = path.join(k8sDir, `${service.replace('.', '-')}-configmap.yaml`);
    if (fs.existsSync(configMapPath)) {
      const processedTemplate = processTemplate(configMapPath);
      await execa.execa('kubectl', ['apply', '-f', '-', '-n', namespace], {
        input: processedTemplate
      });
    }

    // Apply Secrets if they exist
    const secretPath = path.join(k8sDir, `${service.replace('.', '-')}-secrets.yaml`);
    if (fs.existsSync(secretPath)) {
      const processedTemplate = processTemplate(secretPath);
      await execa.execa('kubectl', ['apply', '-f', '-', '-n', namespace], {
        input: processedTemplate
      });
    }

    // Apply Service
    const servicePath = path.join(k8sDir, `${service.replace('.', '-')}-service.yaml`);
    if (fs.existsSync(servicePath)) {
      await runCommand('kubectl', ['apply', '-f', servicePath, '-n', namespace]);
    }

    // Determine which deployment file to use based on environment
    let deploymentFile;
    if (isLocal) {
      const statefulSetLocalPath = path.join(k8sDir, `${service.replace('.', '-')}-statefulset-local.yaml`);
      const deploymentLocalPath = path.join(k8sDir, `${service.replace('.', '-')}-deployment-local.yaml`);

      if (fs.existsSync(statefulSetLocalPath)) {
        deploymentFile = statefulSetLocalPath;
      } else if (fs.existsSync(deploymentLocalPath)) {
        deploymentFile = deploymentLocalPath;
      }
    } else if (isStaging) {
      // Check for staging-specific files first
      const statefulSetStagingPath = path.join(k8sDir, `${service.replace('.', '-')}-statefulset-staging.yaml`);
      const deploymentStagingPath = path.join(k8sDir, `${service.replace('.', '-')}-deployment-staging.yaml`);

      if (fs.existsSync(statefulSetStagingPath)) {
        deploymentFile = statefulSetStagingPath;
      } else if (fs.existsSync(deploymentStagingPath)) {
        deploymentFile = deploymentStagingPath;
      } else {
        // Fall back to production files
        const statefulSetPath = path.join(k8sDir, `${service.replace('.', '-')}-statefulset.yaml`);
        const deploymentPath = path.join(k8sDir, `${service.replace('.', '-')}-deployment.yaml`);

        if (fs.existsSync(statefulSetPath)) {
          deploymentFile = statefulSetPath;
        } else if (fs.existsSync(deploymentPath)) {
          deploymentFile = deploymentPath;
        }
      }
    } else {
      // Production environment
      const statefulSetPath = path.join(k8sDir, `${service.replace('.', '-')}-statefulset.yaml`);
      const deploymentPath = path.join(k8sDir, `${service.replace('.', '-')}-deployment.yaml`);

      if (fs.existsSync(statefulSetPath)) {
        deploymentFile = statefulSetPath;
      } else if (fs.existsSync(deploymentPath)) {
        deploymentFile = deploymentPath;
      }
    }

    // Apply the deployment file if found
    if (deploymentFile) {
      const processedTemplate = processTemplate(deploymentFile);
      await execa.execa('kubectl', ['apply', '-f', '-', '-n', namespace], {
        input: processedTemplate
      });
    } else {
      console.warn(chalk.yellow(`No deployment/statefulset config found for ${service} in ${environment} environment`));
    }

    console.log(chalk.green(`✅ Successfully deployed ${service} for ${environment} to namespace ${namespace}`));
  } catch (error: any) {
    console.error(chalk.red(`Failed to deploy ${service}:`));
    console.error(chalk.red(error.message));
    throw error;
  }
}

/**
 * Apply shared Kubernetes resources
 */
async function applySharedResources(): Promise<void> {
  const sharedK8sDir = path.join(rootDir, 'shared', 'k8s');

  if (!fs.existsSync(sharedK8sDir)) {
    console.warn(chalk.yellow('Shared K8s directory not found, skipping...'));
    return;
  }

  console.log(chalk.green(`\n🔄 Applying shared Kubernetes resources to namespace ${namespace}...\n`));

  try {
    // Apply using kustomize to process all resources defined in kustomization.yaml
    await runCommand('kubectl', ['apply', '-k', sharedK8sDir, '-n', namespace]);
    console.log(chalk.green(`✅ Successfully applied shared resources to namespace ${namespace}`));
  } catch (error: any) {
    console.error(chalk.red('Failed to apply shared resources:'));
    console.error(chalk.red(error.message));
    throw error;
  }
}

/**
 * Clean up exited init containers using Docker directly
 */
async function cleanupDockerInitContainers(): Promise<void> {
  console.log(chalk.green('\n🧹 Removing exited init containers...\n'));

  try {
    // Find all exited containers with names matching init patterns
    const exitedContainers = await execa.execa('docker',
      ['ps', '-a', '--filter', 'status=exited', '--filter', 'name=k8s_init', '--format', '{{.ID}}'],
      { stdio: 'pipe' }
    );

    if (exitedContainers.stdout) {
      const containerIds = exitedContainers.stdout.split('\n').filter(Boolean);

      if (containerIds.length > 0) {
        console.log(chalk.blue(`Found ${containerIds.length} exited init containers to clean up`));

        // Remove all exited init containers
        for (const containerId of containerIds) {
          try {
            await execa.execa('docker', ['rm', containerId], { stdio: 'pipe' });
          } catch (err) {
            // Just continue if we can't remove a container
          }
        }
      }
    }
  } catch (error: any) {
    console.warn(chalk.yellow(`Docker cleanup encountered issues: ${error.message}`));
    // Don't fail the deployment because of cleanup issues
  }
}

/**
 * Remove any leftover containers after scaling/restarting
 */
async function removeLeftoverContainers(): Promise<void> {
  console.log(chalk.green('\n🧹 Checking for leftover containers...\n'));

  try {
    // Wait a moment for Kubernetes to stabilize
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Get all init container IDs
    const allInitContainers = await execa.execa('docker',
      ['ps', '-a', '--filter', 'name=k8s_init', '--format', '{{.ID}} {{.Names}}'],
      { stdio: 'pipe' }
    );

    if (allInitContainers.stdout) {
      const containerInfo = allInitContainers.stdout.split('\n').filter(Boolean);

      // Get current pods
      const podsResult = await execa.execa('kubectl',
        ['get', 'pods', '-n', 'posey', '-o', 'jsonpath={.items[*].metadata.name}'],
        { stdio: 'pipe' }
      );

      const currentPods = podsResult.stdout ? podsResult.stdout.split(' ').filter(Boolean) : [];

      // Find containers that don't belong to any current pod
      const orphanedContainers = containerInfo.filter(info => {
        // Check if container name doesn't include any current pod name
        return !currentPods.some(pod => info.includes(pod));
      });

      if (orphanedContainers.length > 0) {
        console.log(chalk.blue(`Found ${orphanedContainers.length} orphaned init containers to remove`));

        for (const containerInfo of orphanedContainers) {
          const containerId = containerInfo.split(' ')[0];
          try {
            await execa.execa('docker', ['rm', '-f', containerId], { stdio: 'pipe' });
          } catch (err) {
            // Just continue
          }
        }
      }
    }
  } catch (error: any) {
    console.warn(chalk.yellow(`Leftover container cleanup encountered issues: ${error.message}`));
  }
}

/**
 * Clean up non-running init containers without affecting running services
 */
async function cleanupInitContainers(): Promise<void> {
  console.log(chalk.green('\n🧹 Cleaning up non-running init containers...\n'));

  try {
    // Find all non-running init containers
    const exitedContainers = await execa.execa('docker',
      ['ps', '-a', '--filter', 'status=exited', '--filter', 'name=k8s_init', '--format', '{{.ID}} {{.Names}}'],
      { stdio: 'pipe' }
    );

    if (!exitedContainers.stdout) {
      return;
    }

    const containerInfo = exitedContainers.stdout.split('\n').filter(Boolean);

    if (containerInfo.length === 0) {
      return;
    }

    console.log(chalk.blue(`Found ${containerInfo.length} non-running init containers to clean up`));

    // Remove all exited init containers
    let removed = 0;
    for (const info of containerInfo) {
      const containerId = info.split(' ')[0];
      try {
        await execa.execa('docker', ['rm', containerId], { stdio: 'pipe' });
        removed++;
      } catch (err) {
        // Just continue if we can't remove a container
      }
    }

    if (removed > 0) {
      console.log(chalk.green(`Removed ${removed} non-running init containers.`));
    }
  } catch (error: any) {
    console.warn(chalk.yellow(`Container cleanup encountered issues: ${error.message}`));
    // Don't fail the deployment because of cleanup issues
  }
}

/**
 * Main deploy function
 */
async function deploy(): Promise<void> {
  console.log(chalk.blue(`
=================================================
🚀 Starting deployment of Posey Data Services 🚀
=================================================
Environment: ${environment}
Namespace: ${namespace}
=================================================
`));

  try {
    // Create the namespace if it doesn't exist
    try {
      await runCommand('kubectl', ['create', 'namespace', namespace, '--dry-run=client', '-o', 'yaml']);
      await runCommand('kubectl', ['apply', '-f', '-'], {
        input: `apiVersion: v1
kind: Namespace
metadata:
  name: ${namespace}
  labels:
    name: ${namespace}`
      });
    } catch (error) {
      // Namespace might already exist, continue
    }

    // Apply shared resources first
    await applySharedResources();

    // Deploy services
    for (const service of services) {
      await deployService(service);
    }

    console.log(chalk.green(`\n✅ All services deployed successfully for ${environment} to namespace ${namespace}`));

    // Print out service information
    console.log(chalk.cyan('\nService endpoints:'));
    await runCommand('kubectl', ['get', 'services', '-n', 'posey']);

    // Clean up non-running init containers
    await cleanupInitContainers();
  } catch (error: any) {
    console.error(chalk.red('\nDeploy process failed:'));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

// Start the deploy process
deploy().catch(error => {
  console.error(chalk.red('Deployment failed:'));
  console.error(error);
  process.exit(1);
}); 