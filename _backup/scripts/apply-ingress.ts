#!/usr/bin/env node

import { execa } from 'execa';
import path from 'path';
import fs from 'fs';
import chalk from 'chalk';
import { fileURLToPath } from 'url';

// Get the directory name of the current script
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');
const k8sDir = path.resolve(rootDir, 'k8s');
const ingressDir = path.resolve(k8sDir, 'ingress');

// Path to the ingress resources
const namespace = 'posey';

// Data services that need ingress
const dataServices = [
  'postgres',
  'couchbase',
  'vector-db' // Note: The service is called qdrant but the ingress might be named vector-db
];

// Service components that need ingress
const serviceComponents = [
  'agents',
  'auth',
  'cron',
  'mcp',
  'supertokens',
  'voyager'
];

// TCP ports that need forwarding
const tcpPorts: Record<string, number | number[]> = {
  // Data services
  'postgres': 3333,
  'couchbase': [8091, 8092, 8093, 8094, 11210],
  'qdrant': 6334,
  // Application services
  'supertokens': 3567,
  'mcp': 8080
};

async function applyIngressResources() {
  console.log(chalk.blue('================================================='));
  console.log(chalk.blue('🚀 Applying Ingress Resources for Posey Platform 🚀'));
  console.log(chalk.blue('================================================='));

  // Ensure NGINX Ingress Controller is installed
  try {
    const { stdout } = await execa('kubectl', ['get', 'pods', '-n', 'ingress-nginx']);
    if (!stdout.includes('controller')) {
      console.log(chalk.yellow('⚠️ NGINX Ingress Controller not detected. Installing...'));
      await execa('bash', [path.join(ingressDir, 'install-nginx-ingress.sh')], { stdio: 'inherit' });
    } else {
      console.log(chalk.green('✅ NGINX Ingress Controller already installed.'));

      // Even if it's already installed, ensure the TCP services are configured
      console.log(chalk.blue('Ensuring TCP services configuration exists...'));

      // Get existing TCP services ConfigMap
      let existingConfigMap: Record<string, string> = {};
      try {
        const { stdout } = await execa('kubectl', ['get', 'configmap', 'tcp-services', '-n', 'ingress-nginx', '-o', 'json']);
        const config = JSON.parse(stdout);
        existingConfigMap = config.data || {};
      } catch (error) {
        console.log(chalk.yellow('TCP services ConfigMap not found, creating a new one.'));
      }

      // Create or update TCP services ConfigMap
      const tcpServicesConfigMap: {
        apiVersion: string;
        kind: string;
        metadata: {
          name: string;
          namespace: string;
        };
        data: Record<string, string>;
      } = {
        apiVersion: 'v1',
        kind: 'ConfigMap',
        metadata: {
          name: 'tcp-services',
          namespace: 'ingress-nginx'
        },
        data: existingConfigMap
      };

      // Add TCP port mappings
      Object.entries(tcpPorts).forEach(([service, ports]) => {
        const portList = Array.isArray(ports) ? ports : [ports];
        const serviceName = service === 'vector-db' ? 'qdrant' : service;

        portList.forEach(port => {
          tcpServicesConfigMap.data[port.toString()] = `${namespace}/${serviceName}:${port}`;
        });
      });

      // Apply the TCP services ConfigMap
      await execa('kubectl', ['apply', '-f', '-'], {
        input: JSON.stringify(tcpServicesConfigMap),
        stdio: ['pipe', 'inherit', 'inherit']
      });

      // Update the ingress controller to use the TCP services ConfigMap
      console.log(chalk.blue('Ensuring NGINX Ingress Controller is configured for TCP services...'));
      try {
        await execa('kubectl', [
          'patch', 'deployment', 'ingress-nginx-controller',
          '-n', 'ingress-nginx',
          '--type=json',
          '-p', JSON.stringify([{
            op: 'add',
            path: '/spec/template/spec/containers/0/args/-',
            value: '--tcp-services-configmap=$(POD_NAMESPACE)/tcp-services'
          }])
        ], { stdio: 'inherit' });
      } catch (error: any) {
        // This might fail if the argument is already present, which is fine
        console.log(chalk.yellow('Note: TCP services argument might already be configured'));
      }

      // Update the service to expose TCP ports
      console.log(chalk.blue('Ensuring NGINX Ingress Controller service exposes TCP ports...'));
      interface PortPatch {
        op: string;
        path: string;
        value: {
          name: string;
          port: number;
          protocol: string;
          targetPort: number;
        };
      }
      const portPatches: PortPatch[] = [];

      // Create patches for each TCP port
      Object.entries(tcpPorts).forEach(([service, ports]) => {
        const portList = Array.isArray(ports) ? ports : [ports];
        const shortName = service === 'vector-db' ? 'qdrant' :
          (service === 'couchbase' ? 'cb' : service.substring(0, 10));

        portList.forEach((port, idx) => {
          const portName = portList.length > 1 ? `${shortName}-${idx}` : shortName;
          portPatches.push({
            op: 'add',
            path: '/spec/ports/-',
            value: {
              name: portName.substring(0, 15), // Ensure name is 15 chars or less
              port: port,
              protocol: 'TCP',
              targetPort: port
            }
          });
        });
      });

      // Apply the patches
      try {
        await execa('kubectl', [
          'patch', 'service', 'ingress-nginx-controller',
          '-n', 'ingress-nginx',
          '--type=json',
          '-p', JSON.stringify(portPatches)
        ], { stdio: 'inherit' });
      } catch (error: any) {
        // This might fail if the ports are already defined
        console.log(chalk.yellow('Note: TCP ports might already be exposed'));
      }
    }
  } catch (error: any) {
    console.log(chalk.yellow('⚠️ NGINX Ingress Controller not detected. Installing...'));
    await execa('bash', [path.join(ingressDir, 'install-nginx-ingress.sh')], { stdio: 'inherit' });
  }

  // Apply ingress resources for all services
  const allServices = [...dataServices, ...serviceComponents];

  for (const service of allServices) {
    const ingressFile = path.join(ingressDir, `${service}-ingress.yaml`);

    if (fs.existsSync(ingressFile)) {
      console.log(chalk.blue(`Applying ingress resource for ${service}...`));
      try {
        await execa('kubectl', ['apply', '-f', ingressFile, '-n', namespace], { stdio: 'inherit' });
        console.log(chalk.green(`✅ Successfully applied ingress for ${service}`));
      } catch (error: any) {
        console.error(chalk.red(`❌ Failed to apply ingress for ${service}: ${error.message}`));
      }
    } else {
      console.warn(chalk.yellow(`⚠️ No ingress file found for ${service} at ${ingressFile}`));
    }
  }

  // Get all ingresses
  try {
    console.log(chalk.blue('\nAvailable ingress resources:'));
    await execa('kubectl', ['get', 'ingress', '-n', namespace], { stdio: 'inherit' });

    // Get the Ingress Controller IP/hostname
    const { stdout } = await execa('kubectl', ['get', 'svc', '-n', 'ingress-nginx', 'ingress-nginx-controller', '-o', 'jsonpath="{.status.loadBalancer.ingress[0].ip}"']);

    const allDomains = [...dataServices, ...serviceComponents].map(s => `${s}.local.posey.ai`).join(' ');

    if (stdout && stdout !== '""') {
      console.log(chalk.green(`\n✅ Ingress Controller IP: ${stdout.replace(/"/g, '')}`));
      console.log(chalk.blue('Add the following to your /etc/hosts file for local development:'));
      console.log(`${stdout.replace(/"/g, '')} ${allDomains}`);
    } else {
      // For local development with Docker Desktop
      console.log(chalk.green('\n✅ For local development with Docker Desktop, use localhost'));
      console.log(chalk.blue('Add the following to your /etc/hosts file:'));
      console.log(`127.0.0.1 ${allDomains}`);
    }

    // Print connection details
    console.log(chalk.blue('\nData connections:'));
    console.log(chalk.cyan('PostgreSQL: postgresql://pocketprod:PASSWORD@localhost:3333/posey'));
    console.log(chalk.cyan('Couchbase: http://localhost:8091'));
    console.log(chalk.cyan('Qdrant: http://localhost:6334'));

    console.log(chalk.blue('\nService connections:'));
    console.log(chalk.cyan('Supertokens: http://localhost:3567'));
    console.log(chalk.cyan('MCP: http://localhost:8080'));
    console.log(chalk.cyan('Agents: https://agents.local.posey.ai'));
    console.log(chalk.cyan('Auth: https://auth.local.posey.ai'));
    console.log(chalk.cyan('Cron: https://cron.local.posey.ai'));
    console.log(chalk.cyan('Voyager: https://voyager.local.posey.ai'));

    // Add some helpful messages from update-ingress.ts
    console.log(chalk.green('\n✅ Ingress configuration updated successfully'));
    console.log(chalk.yellow('Services are now accessible through:'));
    console.log('  - NodePorts directly');
    console.log('  - Kubernetes port forwarding (use ./port-forward.sh)');
    console.log('  - Ingress paths if DNS is configured');
  } catch (error: any) {
    console.error(chalk.red(`❌ Error retrieving ingress information: ${error.message}`));
  }
}

async function main() {
  console.log(chalk.blue(`Running from ${process.cwd()}`));
  console.log(chalk.blue(`Using ingress directory: ${ingressDir}`));

  try {
    await applyIngressResources();
  } catch (error: any) {
    console.error(chalk.red(`❌ Error: ${error.message}`));
    process.exit(1);
  }
}

// Run the function
main().catch(error => {
  console.error(chalk.red(`❌ Error: ${error.message}`));
  process.exit(1);
}); 