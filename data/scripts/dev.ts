import * as execa from 'execa';
import chalk from 'chalk';
import path from 'path';
import { fileURLToPath } from 'url';
import { clean } from './clean';
import fs from 'fs';
import * as dotenv from 'dotenv';

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
  'postgres',
  'couchbase',
  'vector.db'
];

// Parse arguments
const args = process.argv;
const useIngress = args.includes('--ingress');
const skipPortForward = args.includes('--no-port-forward');
const forceClean = args.includes('--clean'); // Only clean when explicitly requested
const skipClean = !forceClean; // Default to skipping cleanup

// Service port mappings for port forwarding
const servicePorts = {
  'postgres': 3333,
  'couchbase': 8091,
  'qdrant': 1111
};

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
 * Create a port forwarding script for the user to run
 */
async function createPortForwardScript(): Promise<void> {
  const scriptPath = path.join(rootDir, 'port-forward.sh');

  // Create a port-forward script that the user can run manually
  let scriptContent = `#!/bin/bash\n\n`;
  scriptContent += `# Port forwarding script for Posey Data Services\n`;
  scriptContent += `# Run this script to forward local ports to Kubernetes services\n\n`;

  Object.entries(servicePorts).forEach(([service, port]) => {
    const serviceName = service === 'vector.db' ? 'qdrant' : service;
    scriptContent += `echo "Setting up port forwarding for ${service} on localhost:${port}"\n`;
    scriptContent += `kubectl port-forward svc/${serviceName} ${port}:${port} -n posey &\n\n`;
  });

  scriptContent += `echo "Port forwarding is running in the background. Press CTRL+C to stop all port forwards."\n`;
  scriptContent += `echo "Services are now accessible at:"\n`;
  scriptContent += `echo "  - PostgreSQL: localhost:3333"\n`;
  scriptContent += `echo "  - Couchbase:  http://localhost:8091"\n`;
  scriptContent += `echo "  - GraphQL:    http://localhost:4444"\n`;
  scriptContent += `echo "  - Qdrant:     http://localhost:1111"\n\n`;
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
 * Main function to start the development environment
 */
async function dev(): Promise<void> {
  console.log(chalk.green('🚀 Starting Posey Data Services Development Environment'));

  try {
    // First, clean up any existing resources if specifically requested
    if (skipClean) {
      console.log(chalk.yellow('ℹ️ Cleanup is skipped by default to protect platform services.'));
      console.log(chalk.yellow('To force cleanup of data services, use --clean flag.'));
    } else {
      console.log(chalk.red('⚠️ WARNING: Performing cleanup of data services!'));
      await clean();
    }

    // Build all services for local development
    console.log(chalk.yellow('Building local services...'));
    await runCommand('node', ['--loader', 'ts-node/esm', path.join(rootDir, 'scripts', 'build.ts'), '--local'], { cwd: rootDir });

    // Deploy all services for local development
    console.log(chalk.yellow('Deploying local services...'));
    await runCommand('node', ['--loader', 'ts-node/esm', path.join(rootDir, 'scripts', 'deploy.ts'), '--local'], { cwd: rootDir });

    // Setup ingress if requested
    if (useIngress) {
      console.log(chalk.yellow('Setting up local ingress...'));
      try {
        // Use our dedicated script to apply ingress resources
        console.log(chalk.blue('Running apply-ingress script to set up ingress resources...'));
        await runCommand('node', [
          '--loader', 'ts-node/esm',
          path.join(rootDir, 'scripts', 'apply-ingress.ts')
        ], { cwd: rootDir });

        console.log(chalk.green('✅ Ingress set up successfully!'));
        console.log(chalk.yellow('\nDatabase Connection Details:'));
        console.log(chalk.cyan('PostgreSQL: postgresql://pocketprod:PASSWORD@localhost:3333/posey'));
        console.log(chalk.cyan('Couchbase: http://localhost:8091'));
        console.log(chalk.cyan('Qdrant: http://localhost:6334'));
      } catch (error: any) {
        console.error(chalk.red('Failed to set up ingress:'));
        console.error(chalk.red(error.message));
        console.log(chalk.yellow('Continuing with standard services...'));
      }
    }

    // Set up port forwarding for local development
    await createPortForwardScript();

    console.log(chalk.green('✅ All data services are running!'));
    console.log(chalk.cyan('Available services:'));

    services.forEach(service => {
      console.log(chalk.cyan(`  - ${service}`));
    });

    // Display service details
    await runCommand('kubectl', ['get', 'services', '-n', 'posey']);

    console.log(chalk.yellow('\nTo stop the DATA services only, run these commands:'));
    console.log(chalk.cyan('  kubectl delete deployment,statefulset -l component in (postgres,qdrant,couchbase) -n posey'));
    console.log(chalk.cyan('  kubectl delete service postgres qdrant couchbase -n posey --ignore-not-found'));

    // Exit successfully
    process.exit(0);
  } catch (error: any) {
    console.error(chalk.red('Failed to start development environment:'));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

// Start the development environment
dev(); 