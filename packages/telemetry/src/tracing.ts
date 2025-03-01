import { NodeSDK } from '@opentelemetry/sdk-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

let tracerSDK: NodeSDK | undefined;

/**
 * Sets up OpenTelemetry tracing for the application
 * 
 * @param serviceName The name of the service
 * @param serviceNamespace The namespace of the service
 * @param otlpEndpoint The OTLP endpoint URL
 * @param debug Enable debug logging
 */
export function setupTracing(
  serviceName: string,
  serviceNamespace: string,
  otlpEndpoint: string,
  debug: boolean
): void {
  // Create an exporter that sends traces to the OTLP endpoint
  const traceExporter = new OTLPTraceExporter({
    url: `${otlpEndpoint}/v1/traces`,
  });

  // Create a resource that identifies your service
  const resource = new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    [SemanticResourceAttributes.SERVICE_NAMESPACE]: serviceNamespace,
  });

  // Create and start the OpenTelemetry SDK
  tracerSDK = new NodeSDK({
    resource,
    traceExporter,
    instrumentations: [
      getNodeAutoInstrumentations({
        // Enable instrumentation for frameworks, database clients, etc.
        '@opentelemetry/instrumentation-http': { enabled: true },
        '@opentelemetry/instrumentation-express': { enabled: true },
        '@opentelemetry/instrumentation-pg': { enabled: true },
        '@opentelemetry/instrumentation-mongodb': { enabled: true },
      }),
    ],
  });

  // Start the tracer
  tracerSDK.start();

  if (debug) {
    console.log(`Tracing initialized for service ${serviceName} with endpoint ${otlpEndpoint}`);
  }

  // Register shutdown handler
  process.on('SIGTERM', () => {
    if (tracerSDK) {
      tracerSDK.shutdown()
        .then(() => console.log('Tracing terminated'))
        .catch((error) => console.error('Error terminating tracing', error))
        .finally(() => process.exit(0));
    } else {
      process.exit(0);
    }
  });
}

/**
 * Shutdown the tracer gracefully
 */
export async function shutdownTracing(): Promise<void> {
  if (tracerSDK) {
    await tracerSDK.shutdown();
    console.log('Tracing terminated');
  }
}