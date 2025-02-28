import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const k8sDir = path.join(__dirname, 'k8s');
const kubeconfig = path.join(os.homedir(), '.kube', 'config');

function runCommand(command) {
  try {
    execSync(`KUBECONFIG=${kubeconfig} ${command}`, { stdio: 'inherit' });
  } catch (error) {
    console.error(`Error executing command: ${command}`);
    console.error(error);
    process.exit(1);
  }
}

const action = process.argv[2];

if (action === 'up') {
  runCommand(`kubectl apply -f ${k8sDir}`);
} else if (action === 'down') {
  runCommand(`kubectl delete -f ${k8sDir}`);
}