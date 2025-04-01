#!/usr/bin/env node

import { execa } from 'execa';
import path from 'path';
import fs from 'fs';
import chalk from 'chalk';
import { fileURLToPath } from 'url';

// Get file paths using ESM-compatible approach
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');
const ingressDir = path.resolve(rootDir, 'k8s/ingress');
const namespace = 'posey';

// Environment detection
const isLocalDev = process.argv.includes('--local') || process.env.NODE_ENV === 'development';
const domainSuffix = isLocalDev ? 'local.posey.ai' : 'api.posey.ai';

// Service definitions
const dataServices = ['postgres', 'couchbase', 'qdrant'];
const serviceComponents = ['posey-agents', 'posey-auth', 'posey-cron', 'posey-mcp', 'posey-supertokens', 'posey-voyager'];
const tcpPorts = {
  // Data services
  'postgres': 3333,
  'couchbase': [8091, 8092, 8093, 8094, 11210],
  'qdrant': 6334,
  // Application services
  'posey-supertokens': 3567,
  'posey-mcp': 5050,
  'posey-agents': 5555,
  'posey-auth': 9999,
  'posey-cron': 2222,
  'posey-voyager': 7777
};

// Main function
async function main() {
  console.log(chalk.blue('================================================='));
  console.log(chalk.blue(`🚀 Configuring Posey Platform Ingress (${isLocalDev ? 'LOCAL' : 'PRODUCTION'}) 🚀`));
  console.log(chalk.blue('================================================='));

  try {
    // Step 1: Install NGINX Ingress Controller if needed
    await installNginx();

    // Step 2: Configure TCP Services
    await configureTcpServices();

    // Step 3: Apply ingress resources for all services
    const allServices = [...dataServices, ...serviceComponents];
    for (const service of allServices) {
      await applyIngress(service);
    }

    // Step 4: Create port forwarding script for local development
    if (isLocalDev) {
      await createPortForwardScript();
    }

    // Step 5: Show connection information
    await showConnectionInfo();

    console.log(chalk.green('\n✅ Ingress setup complete!'));

    if (isLocalDev) {
      console.log(chalk.blue('\nFor local development:'));
      console.log(chalk.cyan('1. The port-forward-ingress.sh script will be executed automatically after this'));
      console.log(chalk.cyan('2. Update your /etc/hosts file with the entries shown above'));
      console.log(chalk.cyan('3. Access services via http://[service].local.posey.ai:8080 (note the port 8080)'));
      console.log(chalk.cyan('   Standard ports 80/443 require root privileges, so we use 8080/8443 instead'));
    } else {
      console.log(chalk.blue('\nFor production:'));
      console.log(chalk.cyan('1. Configure DNS for your domains to point to the ingress controller IP'));
      console.log(chalk.cyan('2. Access services via https://[service].api.posey.ai'));
    }
  } catch (error) {
    console.error(chalk.red(`\n❌ Error during ingress setup: ${error.message}`));
    process.exit(1);
  }
}

// Install Nginx if not present
async function installNginx() {
  console.log(chalk.blue('\n📦 Checking NGINX Ingress Controller...'));

  try {
    const { stdout } = await execa('kubectl', ['get', 'namespace', 'ingress-nginx']);
    if (stdout.includes('ingress-nginx')) {
      console.log(chalk.green('✅ NGINX Ingress namespace exists'));

      // Check if the controller is running
      try {
        const { stdout } = await execa('kubectl', ['get', 'pods', '-n', 'ingress-nginx', '-l', 'app.kubernetes.io/component=controller']);
        if (stdout.includes('Running')) {
          console.log(chalk.green('✅ NGINX Ingress Controller is running'));
        } else {
          console.log(chalk.yellow('⚠️ NGINX Ingress Controller exists but may not be running properly. Reinstalling...'));
          await execa('bash', [path.join(ingressDir, 'install-nginx-ingress.sh')], { stdio: 'inherit' });
        }
      } catch (error) {
        console.log(chalk.yellow('⚠️ NGINX Ingress Controller not detected. Installing...'));
        await execa('bash', [path.join(ingressDir, 'install-nginx-ingress.sh')], { stdio: 'inherit' });
      }
    } else {
      console.log(chalk.yellow('⚠️ NGINX Ingress namespace not found. Installing...'));
      await execa('bash', [path.join(ingressDir, 'install-nginx-ingress.sh')], { stdio: 'inherit' });
    }
  } catch (error) {
    console.log(chalk.yellow('⚠️ NGINX Ingress namespace not found. Installing...'));
    await execa('bash', [path.join(ingressDir, 'install-nginx-ingress.sh')], { stdio: 'inherit' });
  }

  // Ensure nginx is fully ready before proceeding
  console.log(chalk.blue('Ensuring NGINX Ingress Controller is fully ready...'));
  try {
    await execa('kubectl', ['wait', '--namespace', 'ingress-nginx',
      '--for=condition=available', 'deployment/ingress-nginx-controller',
      '--timeout=180s'], { stdio: 'inherit' });

    console.log(chalk.green('✅ NGINX Ingress Controller is ready'));
  } catch (error) {
    console.log(chalk.yellow('⚠️ Timed out waiting for NGINX. Continuing anyway, but you may need to rerun this script.'));
  }
}

// Configure TCP services
async function configureTcpServices() {
  console.log(chalk.blue('\n🔌 Configuring TCP services...'));

  // Get existing ConfigMap
  let existingData = {};
  try {
    const { stdout } = await execa('kubectl', ['get', 'configmap', 'tcp-services', '-n', 'ingress-nginx', '-o', 'json']);
    existingData = JSON.parse(stdout).data || {};
  } catch (error) {
    console.log(chalk.yellow('TCP services ConfigMap not found, creating a new one.'));
  }

  // Create ConfigMap
  const configMap = {
    apiVersion: 'v1',
    kind: 'ConfigMap',
    metadata: {
      name: 'tcp-services',
      namespace: 'ingress-nginx'
    },
    data: existingData
  };

  // Add port mappings
  Object.entries(tcpPorts).forEach(([service, ports]) => {
    const portList = Array.isArray(ports) ? ports : [ports];
    portList.forEach(port => {
      configMap.data[port.toString()] = `${namespace}/${service}:${port}`;
    });
  });

  // Apply ConfigMap
  console.log(chalk.blue('Applying TCP services ConfigMap...'));
  await execa('kubectl', ['apply', '-f', '-'], {
    input: JSON.stringify(configMap),
    stdio: ['pipe', 'inherit', 'inherit']
  });

  // Update controller args
  console.log(chalk.blue('Configuring NGINX Ingress Controller to use TCP services...'));
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
  } catch (error) {
    console.log(chalk.yellow('TCP services argument might already be configured'));
  }

  // Check existing ports in the service
  console.log(chalk.blue('Checking existing ports in NGINX Ingress Controller service...'));
  let existingPorts = [];
  try {
    const { stdout } = await execa('kubectl', [
      'get', 'service', 'ingress-nginx-controller',
      '-n', 'ingress-nginx',
      '-o', 'json'
    ]);
    const serviceData = JSON.parse(stdout);
    existingPorts = (serviceData.spec.ports || []).map(port => {
      return {
        name: port.name || '',
        port: port.port
      };
    });
    console.log(chalk.green(`Found ${existingPorts.length} existing ports in service`));
  } catch (error) {
    console.log(chalk.yellow('Could not retrieve existing ports, will try to add all ports'));
  }

  // Expose TCP ports - only add ports that don't already exist
  console.log(chalk.blue('Exposing TCP ports on NGINX Ingress Controller service...'));
  const portPatches = [];
  Object.entries(tcpPorts).forEach(([service, ports]) => {
    const portList = Array.isArray(ports) ? ports : [ports];
    const shortName = service.substring(0, 10);

    portList.forEach(port => {
      // Check if this port already exists in the service
      const portExists = existingPorts.some(existingPort => existingPort.port === port);
      if (!portExists) {
        console.log(chalk.blue(`Adding port ${port} for ${service}...`));
        portPatches.push({
          op: 'add',
          path: '/spec/ports/-',
          value: {
            name: `${shortName}-${port}`.substring(0, 15),
            port: port,
            protocol: 'TCP',
            targetPort: port
          }
        });
      } else {
        console.log(chalk.green(`Port ${port} already exists in service, skipping`));
      }
    });
  });

  // Only apply the patch if there are ports to add
  if (portPatches.length > 0) {
    try {
      console.log(chalk.blue(`Adding ${portPatches.length} new ports to service...`));
      await execa('kubectl', [
        'patch', 'service', 'ingress-nginx-controller',
        '-n', 'ingress-nginx',
        '--type=json',
        '-p', JSON.stringify(portPatches)
      ], { stdio: 'inherit' });
    } catch (error) {
      console.error(chalk.red(`Error adding ports: ${error.message}`));
    }
  } else {
    console.log(chalk.green('No new ports to add, all required ports already exist in service'));
  }

  // Ensure all services are ClusterIP type for ingress
  console.log(chalk.blue('Converting services to ClusterIP type...'));
  const allServices = [...dataServices, ...serviceComponents];
  for (const service of allServices) {
    try {
      await execa('kubectl', ['get', 'svc', service, '-n', namespace]);
      await execa('kubectl', ['patch', 'svc', service, '-n', namespace, '-p', '{"spec": {"type": "ClusterIP"}}']);
    } catch (error) {
      console.log(chalk.yellow(`Service ${service} not found or already configured properly`));
    }
  }

  // Restart NGINX to apply changes
  console.log(chalk.blue('Restarting NGINX Ingress Controller to apply TCP configuration...'));
  await execa('kubectl', ['rollout', 'restart', 'deployment/ingress-nginx-controller', '-n', 'ingress-nginx'], { stdio: 'inherit' });
  await execa('kubectl', ['rollout', 'status', 'deployment/ingress-nginx-controller', '-n', 'ingress-nginx', '--timeout=180s'], { stdio: 'inherit' });
}

// Apply ingress for a service
async function applyIngress(service) {
  // For service names with posey- prefix, strip it for the ingress file name
  const ingressName = service.startsWith('posey-') ? service.substring(6) : service;
  const ingressFile = path.join(ingressDir, `${ingressName}-ingress.yaml`);

  if (fs.existsSync(ingressFile)) {
    console.log(chalk.blue(`\n🌐 Applying ingress for ${service}...`));

    try {
      if (isLocalDev) {
        // Modify domain for local development
        let content = fs.readFileSync(ingressFile, 'utf8');
        content = content.replace(/api\.posey\.ai/g, 'local.posey.ai');

        const tempFile = path.join(ingressDir, `${ingressName}-ingress-temp.yaml`);
        fs.writeFileSync(tempFile, content);

        await execa('kubectl', ['apply', '-f', tempFile, '-n', namespace], { stdio: 'inherit' });
        fs.unlinkSync(tempFile);
      } else {
        await execa('kubectl', ['apply', '-f', ingressFile, '-n', namespace], { stdio: 'inherit' });
      }

      console.log(chalk.green(`✅ Applied ingress for ${service}`));
    } catch (error) {
      console.error(chalk.red(`❌ Failed to apply ingress for ${service}: ${error.message}`));
    }
  } else {
    console.warn(chalk.yellow(`⚠️ No ingress file found for ${service} at ${ingressFile}`));
  }
}

// Create port forward script
async function createPortForwardScript() {
  console.log(chalk.blue('\n📝 Creating port forwarding scripts...'));

  // Create direct port-forward script for services
  const scriptPath = path.resolve(rootDir, 'scripts/port-forward-all.sh');
  let script = '#!/bin/bash\n\n# Auto-generated port forwarding script\n\n';

  Object.entries(tcpPorts).forEach(([service, ports]) => {
    const portList = Array.isArray(ports) ? ports : [ports];
    portList.forEach(port => {
      script += `kubectl port-forward service/${service} ${port}:${port} -n ${namespace} &\n`;
    });
  });

  script += '\necho "Port forwarding started. Press Ctrl+C to stop."\n';
  script += 'trap "kill 0" EXIT\nwait\n';

  fs.writeFileSync(scriptPath, script);
  fs.chmodSync(scriptPath, '755');
  console.log(chalk.green(`✅ Created service port forwarding script at ${scriptPath}`));

  // Create ingress port-forward script
  const ingressScriptPath = path.resolve(rootDir, 'scripts/port-forward-ingress.sh');
  let ingressScript = `#!/bin/bash

# Port forward the NGINX ingress controller for local development
# This allows you to use domain names instead of direct service port forwards

# Kill any existing port-forwards
pkill -f "kubectl port-forward.*ingress-nginx" || true

# Forward HTTP and HTTPS ports (use non-privileged ports)
echo "Forwarding HTTP/HTTPS ports..."
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80 8443:443 &
echo "Access services at http://[service].${domainSuffix}:8080"

# Get list of ports defined in the service
echo "Checking available TCP ports in ingress-nginx-controller service..."
AVAILABLE_PORTS=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o json | jq -r '.spec.ports[].port')

`;

  // Add TCP port forwards for databases
  ingressScript += '# Forward database ports if they\'re defined in the service\n';
  ingressScript += 'echo "Forwarding database ports..."\n';
  Object.entries(tcpPorts)
    .filter(([service]) => dataServices.includes(service))
    .forEach(([service, ports]) => {
      const portList = Array.isArray(ports) ? ports : [ports];
      portList.forEach(port => {
        ingressScript += `if echo "$AVAILABLE_PORTS" | grep -q "^${port}$"; then\n`;
        ingressScript += `  echo "Forwarding port ${port}..."\n`;
        ingressScript += `  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller ${port}:${port} & # ${service}\n`;
        ingressScript += `else\n`;
        ingressScript += `  echo "Skipping port ${port} (not defined in service)"\n`;
        ingressScript += `fi\n`;
      });
    });

  // Add TCP port forwards for application services
  ingressScript += '\n# Forward application service ports if they\'re defined in the service\n';
  ingressScript += 'echo "Forwarding application ports..."\n';
  Object.entries(tcpPorts)
    .filter(([service]) => serviceComponents.includes(service))
    .forEach(([service, ports]) => {
      const portList = Array.isArray(ports) ? ports : [ports];
      portList.forEach(port => {
        ingressScript += `if echo "$AVAILABLE_PORTS" | grep -q "^${port}$"; then\n`;
        ingressScript += `  echo "Forwarding port ${port}..."\n`;
        ingressScript += `  kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller ${port}:${port} & # ${service}\n`;
        ingressScript += `else\n`;
        ingressScript += `  echo "Skipping port ${port} (not defined in service)"\n`;
        ingressScript += `fi\n`;
      });
    });

  // Add hosts file entries
  const allDomains = [...dataServices, ...serviceComponents].map(s => `${s}.${domainSuffix}`).join(' ');

  ingressScript += `
echo ""
echo "Ingress port forwarding started"
echo "Add these entries to your /etc/hosts file if not already present:"
echo "127.0.0.1 ${allDomains}"
echo ""
echo "You can now access services via:"
echo "- http://[service].${domainSuffix}:8080"
echo "- Direct TCP ports (PostgreSQL, Couchbase, etc.)"
echo ""
echo "Press Ctrl+C to stop all port forwards"

# Cleanup when script is terminated
trap "echo 'Stopping all port forwards'; kill 0" EXIT SIGINT SIGTERM

# Wait for all port forwards
wait`;

  fs.writeFileSync(ingressScriptPath, ingressScript);
  fs.chmodSync(ingressScriptPath, '755');
  console.log(chalk.green(`✅ Created ingress port forwarding script at ${ingressScriptPath}`));
}

// Show connection info
async function showConnectionInfo() {
  console.log(chalk.blue('\n📊 Ingress Resources:'));
  await execa('kubectl', ['get', 'ingress', '-n', namespace], { stdio: 'inherit' });

  try {
    const { stdout } = await execa('kubectl', ['get', 'svc', '-n', 'ingress-nginx', 'ingress-nginx-controller', '-o', 'jsonpath="{.status.loadBalancer.ingress[0].ip}"']);

    // Generate list of domain names (strip posey- prefix for domain names)
    const allServiceDomains = [
      ...dataServices.map(s => `${s}.${domainSuffix}`),
      ...serviceComponents.map(s => {
        const serviceName = s.startsWith('posey-') ? s.substring(6) : s;
        return `${serviceName}.${domainSuffix}`;
      })
    ];
    const domains = allServiceDomains.join(' ');

    console.log(chalk.blue('\n🌍 Connection Information:'));

    if (stdout && stdout !== '""') {
      console.log(chalk.green(`\n✅ Ingress Controller IP: ${stdout.replace(/"/g, '')}`));
      console.log(chalk.blue('Add to /etc/hosts:'));
      console.log(`${stdout.replace(/"/g, '')} ${domains}`);
    } else {
      console.log(chalk.green('\n✅ For local development with Docker Desktop, use localhost'));
      console.log(chalk.blue('Add to /etc/hosts:'));
      console.log(`127.0.0.1 ${domains}`);
    }

    // Print connection info
    console.log(chalk.cyan('\n📦 Data Services:'));
    console.log(`PostgreSQL: localhost:${tcpPorts.postgres}`);

    if (Array.isArray(tcpPorts.couchbase)) {
      console.log(`Couchbase: http://localhost:${tcpPorts.couchbase[0]}`);
    }

    console.log(`Qdrant: http://localhost:${tcpPorts.qdrant}`);

    console.log(chalk.cyan('\n🚀 Application Services:'));
    for (const service of serviceComponents) {
      const port = Array.isArray(tcpPorts[service]) ? tcpPorts[service][0] : tcpPorts[service];
      const serviceName = service.startsWith('posey-') ? service.substring(6) : service;

      if (isLocalDev) {
        console.log(`${serviceName}: http://localhost:${port} or http://${serviceName}.${domainSuffix}:8080`);
      } else {
        console.log(`${serviceName}: http://localhost:${port} or http://${serviceName}.${domainSuffix}`);
      }
    }
  } catch (error) {
    console.error(chalk.red(`❌ Error retrieving connection info: ${error.message}`));
  }
}

// Run the script
main().catch(error => {
  console.error(chalk.red(`❌ Error: ${error.message}`));
  process.exit(1);
}); 