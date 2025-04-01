#!/usr/bin/env node

import chalk from 'chalk';
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

// Get the directory name of the current script
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

console.log(chalk.blue('================================================='));
console.log(chalk.blue('🚀 Updating Posey Platform Ingress Configuration 🚀'));
console.log(chalk.blue('================================================='));

// Run ingress configuration from data directory
try {
  console.log(chalk.yellow('\nRunning ingress setup with direct execution...'));

  // Execute the yarn ingress command in the data directory
  process.chdir(path.join(rootDir, 'data'));
  console.log(chalk.blue(`Working directory: ${process.cwd()}`));

  execSync('yarn ingress', { stdio: 'inherit' });

  console.log(chalk.green('\n✅ Ingress configuration updated successfully'));
  console.log(chalk.yellow('Services are now accessible through:'));
  console.log('  - NodePorts directly');
  console.log('  - Kubernetes port forwarding (use ./port-forward.sh)');
  console.log('  - Ingress paths if DNS is configured');

  // Get the ingress controller IP
  let ingressIp = '';
  try {
    ingressIp = execSync('kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath="{.status.loadBalancer.ingress[0].ip}"', { encoding: 'utf8' }).trim();
  } catch (err) {
    console.log(chalk.yellow('\nNo external IP found for ingress controller.'));
  }

  if (ingressIp && ingressIp !== '""') {
    console.log(chalk.yellow(`\nIngress Controller IP: ${ingressIp}`));
    console.log('Add the following to your /etc/hosts file:');
    console.log(`${ingressIp} postgres.local.posey.ai couchbase.local.posey.ai qdrant.local.posey.ai agents.local.posey.ai auth.local.posey.ai cron.local.posey.ai mcp.local.posey.ai supertokens.local.posey.ai voyager.local.posey.ai`);
  } else {
    console.log(chalk.yellow('\nNo external IP found for ingress controller.'));
    console.log('For local development, add to your /etc/hosts file:');
    console.log('127.0.0.1 postgres.local.posey.ai couchbase.local.posey.ai qdrant.local.posey.ai agents.local.posey.ai auth.local.posey.ai cron.local.posey.ai mcp.local.posey.ai supertokens.local.posey.ai voyager.local.posey.ai');
  }
} catch (error) {
  console.error(chalk.red('\n❌ Failed to update ingress configuration'));
  console.error(chalk.red(`Error: ${error.message}`));
  console.log('Try running manually from data directory:');
  console.log(`cd ${path.join(rootDir, 'data')} && yarn ingress`);
  process.exit(1);
}
