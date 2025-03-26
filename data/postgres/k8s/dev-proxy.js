#!/usr/bin/env node

import { execSync, spawn } from 'child_process';
// import { createInterface } from 'readline';

// Define services and their ports
const services = [
  { name: 'postgres', namespace: 'posey', k8sPort: 3333, localPort: 3333 },
  // Add other services as they're migrated to Kubernetes
  // { name: 'qdrant', namespace: 'posey', k8sPort: 1111, localPort: 1111 },
  // { name: 'agents', namespace: 'posey', k8sPort: 5555, localPort: 5555 },
];

// Maximum wait time in seconds for pods to be ready
const MAX_WAIT_TIME = 60; // Reduced to catch issues faster

// Check if Kubernetes is running
try {
  execSync('kubectl cluster-info', { stdio: 'ignore' });
  console.log('✅ Connected to Kubernetes cluster');
} catch (error) {
  console.error('❌ Could not connect to Kubernetes cluster. Is it running?');
  process.exit(1);
}

// Get more detailed information about pod status
function getPodDetails(service) {
  try {
    // Get the pod name
    const podName = execSync(
      `kubectl get pods -n ${service.namespace} -l app=${service.name} -o jsonpath='{.items[0].metadata.name}'`,
      { encoding: 'utf8' }
    ).trim();

    if (!podName) {
      return "No pods found with this label";
    }

    // Check for common issues

    // 1. Check PVC status if pod is Pending
    try {
      const pvcs = execSync(
        `kubectl get pvc -n ${service.namespace} -o jsonpath='{range .items[*]}{.metadata.name}{": "}{.status.phase}{", "}{end}'`,
        { encoding: 'utf8' }
      ).trim();

      if (pvcs.includes("Pending")) {
        return `PVC issue detected: ${pvcs}`;
      }
    } catch (e) {
      // Ignore PVC check errors
    }

    // 2. Check scheduling issues
    try {
      const events = execSync(
        `kubectl get events -n ${service.namespace} --field-selector involvedObject.name=${podName} -o jsonpath='{range .items[*]}{.reason}{": "}{.message}{"\n"}{end}'`,
        { encoding: 'utf8' }
      ).trim();

      if (events.includes("FailedScheduling")) {
        return `Scheduling issue detected: ${events}`;
      }
    } catch (e) {
      // Ignore events check errors
    }

    // 3. Full describe output for detailed diagnosis
    try {
      return execSync(
        `kubectl describe pod ${podName} -n ${service.namespace}`,
        { encoding: 'utf8' }
      ).trim();
    } catch (e) {
      return "Could not get pod details";
    }
  } catch (error) {
    return `Error getting pod details: ${error.message}`;
  }
}

// Wait for pod to be in Running state
async function waitForPod(service) {
  console.log(`⏳ Waiting for ${service.name} pod to be ready (max ${MAX_WAIT_TIME}s)...`);

  let pendingTimeCounter = 0;

  for (let i = 0; i < MAX_WAIT_TIME; i++) {
    try {
      const podStatus = execSync(
        `kubectl get pods -n ${service.namespace} -l app=${service.name} -o jsonpath='{.items[0].status.phase}'`,
        { encoding: 'utf8' }
      ).trim();

      if (podStatus === 'Running') {
        console.log(`✅ ${service.name} pod is running!`);
        return true;
      }

      // If pod is in Pending state for more than 15 seconds, start investigating
      if (podStatus === 'Pending') {
        pendingTimeCounter++;

        if (pendingTimeCounter >= 15) {
          console.log(`⚠️ ${service.name} pod has been in Pending state for ${pendingTimeCounter} seconds. Investigating...`);
          console.log('---------------------------------------------------');
          console.log(getPodDetails(service));
          console.log('---------------------------------------------------');
          console.log(`Run this command for more details: kubectl describe pod -n ${service.namespace} -l app=${service.name}`);

          // Only show detailed diagnostics once to avoid spam
          pendingTimeCounter = 0;
        }
      }

      // If not running yet, report current status every 5 seconds
      if (i % 5 === 0) {
        try {
          const containerStatus = execSync(
            `kubectl get pods -n ${service.namespace} -l app=${service.name} -o jsonpath='{.items[0].status.containerStatuses[0].state}'`,
            { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }
          ).trim();
          console.log(`⏳ ${service.name} pod status: ${podStatus} (${i}s elapsed)`);

          // If there's a container status with waiting reason, show that
          if (containerStatus && containerStatus.includes('waiting')) {
            try {
              const waitingReason = execSync(
                `kubectl get pods -n ${service.namespace} -l app=${service.name} -o jsonpath='{.items[0].status.containerStatuses[0].state.waiting.reason}'`,
                { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }
              ).trim();
              console.log(`   Reason: ${waitingReason}`);

              if (waitingReason === 'ImagePullBackOff' || waitingReason === 'ErrImagePull') {
                console.log(`⚠️ Image pull issue detected! Make sure you've built the image with: npm run build:local`);
              }
            } catch (e) {
              // Ignore errors in getting detailed reason
            }
          }
        } catch (error) {
          console.log(`⏳ Status check error: ${error.message}`);
        }
      }

      // Wait 1 second before checking again
      await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
      console.log(`⏳ Waiting for ${service.name} pod to be created... (${i}s elapsed)`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  console.error(`❌ Timed out waiting for ${service.name} pod to be ready`);
  return false;
}

// Start port-forwarding for a service
function startPortForward(service) {
  console.log(`🔄 Starting port-forward for ${service.name} on port ${service.localPort}`);

  const process = spawn('kubectl', [
    'port-forward',
    '-n', service.namespace,
    `service/${service.name}`,
    `${service.localPort}:${service.k8sPort}`
  ], {
    stdio: ['ignore', 'pipe', 'pipe']
  });

  process.stdout.on('data', (data) => {
    console.log(`[${service.name}] ${data.toString().trim()}`);
  });

  process.stderr.on('data', (data) => {
    console.error(`[${service.name}] ${data.toString().trim()}`);
  });

  process.on('close', (code) => {
    if (code !== 0) {
      console.log(`⛔ ${service.name} port-forward exited with code ${code}`);
      console.log(`🔄 Attempting to restart port-forward for ${service.name} in 5 seconds...`);
      setTimeout(() => startPortForward(service), 5000);
    } else {
      console.log(`⛔ ${service.name} port-forward stopped`);
    }
  });

  return process;
}

// Main function to start everything
async function main() {
  const activeProcesses = [];

  // Wait for all pods to be ready before starting port-forwarding
  for (const service of services) {
    const ready = await waitForPod(service);
    if (ready) {
      const process = startPortForward(service);
      activeProcesses.push({ service, process });
    } else {
      console.log(`⚠️ Skipping port-forward for ${service.name} as pod is not ready`);
    }
  }

  if (activeProcesses.length === 0) {
    console.error('❌ No services could be started. Check pod status with: kubectl get pods -n posey');
    process.exit(1);
  }

  console.log('\n✅ Port-forwarding started. Press Ctrl+C to stop all services.');
  console.log('📊 Available services:');
  activeProcesses.forEach(({ service }) => {
    console.log(`   - ${service.name}: localhost:${service.localPort}`);
  });

  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down all port-forwards...');
    activeProcesses.forEach(({ service, process }) => {
      process.kill();
      console.log(`   - ${service.name}: stopped`);
    });
    process.exit(0);
  });
}

// Run the main function
main().catch(error => {
  console.error('❌ Error in dev proxy:', error);
  process.exit(1);
}); 