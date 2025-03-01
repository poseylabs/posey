import { diag, DiagLogLevel } from '@opentelemetry/api';
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-http';
import { LoggerProvider, SimpleLogRecordProcessor } from '@opentelemetry/sdk-logs';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

let loggerProvider: LoggerProvider | undefined;

/**
 * Sets up OpenTelemetry logging for the application
 * 
 * @param serviceName The name of the service
 * @param serviceNamespace The namespace of the service
 * @param otlpEndpoint The OTLP endpoint URL
 * @param debug Enable debug logging
 */
export function setupLogging(
  serviceName: string,
  serviceNamespace: string,
  otlpEndpoint: string,
  debug: boolean
): void {
  // Set the diagnostic logging level if debug is enabled
  if (debug) {
    diag.setLogger({
      verbose: (...args) => console.log('[OTEL Verbose]', ...args),
      debug: (...args) => console.log('[OTEL Debug]', ...args),
      info: (...args) => console.log('[OTEL Info]', ...args),
      warn: (...args) => console.log('[OTEL Warn]', ...args),
      error: (...args) => console.log('[OTEL Error]', ...args),
    }, DiagLogLevel.DEBUG);
  }

  // Create a resource that identifies your service
  const resource = new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    [SemanticResourceAttributes.SERVICE_NAMESPACE]: serviceNamespace,
  });

  // Create an exporter that sends logs to the OTLP endpoint
  const logExporter = new OTLPLogExporter({
    url: `${otlpEndpoint}/v1/logs`,
  });

  // Create and configure the logger provider
  loggerProvider = new LoggerProvider({
    resource,
  });

  // Add the exporter to the logger provider
  loggerProvider.addLogRecordProcessor(new SimpleLogRecordProcessor(logExporter));

  // Register the logger provider
  loggerProvider.register();

  if (debug) {
    console.log(`Logging initialized for service ${serviceName} with endpoint ${otlpEndpoint}`);
  }
}

/**
 * Shutdown the logging provider gracefully
 */
export async function shutdownLogging(): Promise<void> {
  if (loggerProvider) {
    await loggerProvider.shutdown();
    console.log('Logging terminated');
  }
} 