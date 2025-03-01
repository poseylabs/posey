import { setupTracing, shutdownTracing } from './tracing';
import { setupMetrics, shutdownMetrics } from './metrics';
import { setupLogging, shutdownLogging } from './logging';

export interface TelemetryOptions {
  serviceName: string;
  serviceNamespace?: string;
  otlpEndpoint?: string;
  debug?: boolean;
}

/**
 * Initialize OpenTelemetry instrumentation for a service
 * 
 * @param options Configuration options for telemetry
 */
export async function initTelemetry(options: TelemetryOptions): Promise<void> {
  const {
    serviceName,
    serviceNamespace = 'posey',
    otlpEndpoint = 'http://localhost:4318',
    debug = false
  } = options;

  if (debug) {
    console.log(`Initializing telemetry for service: ${serviceName}`);
  }

  // Initialize tracing
  setupTracing(serviceName, serviceNamespace, otlpEndpoint, debug);

  // Initialize metrics
  setupMetrics(serviceName, serviceNamespace, otlpEndpoint, debug);

  // Initialize logging
  setupLogging(serviceName, serviceNamespace, otlpEndpoint, debug);
}

/**
 * Shutdown all telemetry components gracefully
 */
export async function shutdownTelemetry(): Promise<void> {
  await Promise.all([
    shutdownTracing(),
    shutdownMetrics(),
    shutdownLogging()
  ]);

  console.log('All telemetry components shut down');
}

// Export individual components for advanced usage
export * from './tracing';
export * from './metrics';
export * from './logging'; 