#!/usr/bin/env ts-node

import * as execa from 'execa';
import chalk from 'chalk';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

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
 * Main function to start the production environment
 */
async function start(): Promise<void> {
  console.log(chalk.green('🚀 Starting Posey Data Services Production Environment'));

  try {
    // Build all services for production
    console.log(chalk.yellow('Building production services...'));
    await runCommand('ts-node', [path.join(rootDir, 'scripts', 'build.ts')], { cwd: rootDir });

    // Deploy all services for production
    console.log(chalk.yellow('Deploying production services...'));
    await runCommand('ts-node', [path.join(rootDir, 'scripts', 'deploy.ts')], { cwd: rootDir });

    console.log(chalk.green('✅ All production data services are running!'));

    // Display services and their status
    await runCommand('kubectl', ['get', 'pods', '-n', 'posey']);

    console.log(chalk.yellow('\nPress Ctrl+C to exit the monitoring'));

    // Keep monitoring the pods
    await runCommand('kubectl', ['get', 'pods', '-n', 'posey', '-w']);
  } catch (error: any) {
    console.error(chalk.red('Failed to start production environment:'));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

// Start the production environment
start(); 