# @posey/telemetry

A shared library for OpenTelemetry instrumentation in the Posey project.

## Features

- Unified tracing, metrics, and logging setup
- Configurable OTLP endpoint for sending telemetry data
- Simple API for service instrumentation
- Graceful shutdown handling

## Installation

```bash
# From the root of the monorepo
nx build telemetry
```

## Usage

### Basic Usage

```typescript
import { initTelemetry, shutdownTelemetry } from '@posey/telemetry';

// Initialize telemetry at application startup
await initTelemetry({
  serviceName: 'my-service',
  // Optional parameters with defaults
  serviceNamespace: 'posey',
  otlpEndpoint: 'http://localhost:4318',
  debug: false
});

// Your application code here...

// Shutdown telemetry before application exit
process.on('SIGTERM', async () => {
  await shutdownTelemetry();
  process.exit(0);
});
```

### Advanced Usage

You can also use the individual components directly:

```typescript
import { 
  setupTracing, 
  setupMetrics, 
  setupLogging,
  shutdownTracing,
  shutdownMetrics,
  shutdownLogging
} from '@posey/telemetry';

// Initialize only tracing
setupTracing(
  'my-service',
  'posey',
  'http://localhost:4318',
  true // debug mode
);

// Shutdown only tracing
await shutdownTracing();
```

## Integration with OpenTelemetry Collector

This library is designed to work with the OpenTelemetry Collector. The collector should be configured to receive telemetry data on the endpoint specified in the `otlpEndpoint` parameter.

Example collector configuration:

```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
  
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
```

## Environment Variables

The library can be configured using environment variables:

- `OTEL_SERVICE_NAME`: Service name (overrides the serviceName parameter)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTLP endpoint (overrides the otlpEndpoint parameter)
- `OTEL_LOG_LEVEL`: Log level for the OpenTelemetry SDK

## License

MIT 