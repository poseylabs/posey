import * as execa from 'execa';
import chalk from 'chalk';
import path from 'path';
import { fileURLToPath } from 'url';
import { clean } from './clean';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

const services = [
  'postgres',
  'couchbase',
  'vector.db',
  'graphql'
];

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
 * Main function to start the development environment
 */
async function dev(): Promise<void> {
  console.log(chalk.green('🚀 Starting Posey Data Services Development Environment'));

  try {
    // First, clean up any existing resources
    await clean();

    // Build all services for local development
    console.log(chalk.yellow('Building local services...'));
    await runCommand('node', ['--loader', 'ts-node/esm', path.join(rootDir, 'scripts', 'build.ts'), '--local'], { cwd: rootDir });

    // Deploy all services for local development
    console.log(chalk.yellow('Deploying local services...'));
    await runCommand('node', ['--loader', 'ts-node/esm', path.join(rootDir, 'scripts', 'deploy.ts'), '--local'], { cwd: rootDir });

    console.log(chalk.green('✅ All data services are running!'));
    console.log(chalk.cyan('Available services:'));

    services.forEach(service => {
      console.log(chalk.cyan(`  - ${service}`));
    });

    // Display service details
    await runCommand('kubectl', ['get', 'services', '-n', 'posey']);

    console.log(chalk.yellow('\nTo stop the services, run: kubectl delete -n posey deployment,statefulset,service --all'));

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