import { MeterProvider } from '@opentelemetry/sdk-metrics';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';

let meterProvider: MeterProvider | undefined;

/**
 * Sets up OpenTelemetry metrics for the application
 * 
 * @param serviceName The name of the service
 * @param serviceNamespace The namespace of the service
 * @param otlpEndpoint The OTLP endpoint URL
 * @param debug Enable debug logging
 */
export function setupMetrics(
  serviceName: string,
  serviceNamespace: string,
  otlpEndpoint: string,
  debug: boolean
): void {
  // Create an exporter that sends metrics to the OTLP endpoint
  const metricExporter = new OTLPMetricExporter({
    url: `${otlpEndpoint}/v1/metrics`,
  });

  // Create a resource that identifies your service
  const resource = new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    [SemanticResourceAttributes.SERVICE_NAMESPACE]: serviceNamespace,
  });

  // Create and configure the meter provider
  meterProvider = new MeterProvider({
    resource,
  });

  // Add the exporter to the meter provider
  meterProvider.addMetricReader(metricExporter);

  // Set the global meter provider
  meterProvider.register();

  if (debug) {
    console.log(`Metrics initialized for service ${serviceName} with endpoint ${otlpEndpoint}`);
  }
}

/**
 * Shutdown the metrics provider gracefully
 */
export async function shutdownMetrics(): Promise<void> {
  if (meterProvider) {
    await meterProvider.shutdown();
    console.log('Metrics terminated');
  }
} 