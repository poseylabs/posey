import { initTelemetry, shutdownTelemetry } from '../src';
import { trace, context, SpanStatusCode } from '@opentelemetry/api';

async function main() {
  // Initialize telemetry
  await initTelemetry({
    serviceName: 'example-service',
    debug: true
  });

  console.log('Telemetry initialized. Starting example...');

  // Get a tracer
  const tracer = trace.getTracer('example-tracer');

  // Create a span
  const span = tracer.startSpan('main-operation');

  // Use the span in a context
  await context.with(trace.setSpan(context.active(), span), async () => {
    try {
      // Create a child span
      const childSpan = tracer.startSpan('child-operation');

      // Add attributes to the span
      childSpan.setAttribute('operation.type', 'example');
      childSpan.setAttribute('operation.id', '12345');

      // Simulate some work
      console.log('Performing operation...');
      await simulateWork(500);

      // Add an event to the span
      childSpan.addEvent('operation.completed', {
        duration_ms: 500
      });

      // End the child span
      childSpan.end();
    } catch (error) {
      // Record error in the span
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error instanceof Error ? error.message : 'Unknown error'
      });
      console.error('Operation failed:', error);
    }
  });

  // End the parent span
  span.end();

  console.log('Example completed. Shutting down telemetry...');

  // Shutdown telemetry
  await shutdownTelemetry();
}

// Helper function to simulate async work
function simulateWork(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Run the example
main().catch(error => {
  console.error('Example failed:', error);
  process.exit(1);
});

