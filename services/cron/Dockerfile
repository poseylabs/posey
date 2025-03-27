# Build stage
FROM node:20-slim AS builder

WORKDIR /app

# Configure npm for better network resilience
RUN npm config set fetch-retries 5 \
  && npm config set fetch-retry-mintimeout 10000 \
  && npm config set fetch-retry-maxtimeout 60000 \
  && npm config set registry https://registry.npmjs.org/

# Copy only the necessary files for the cron service
COPY services/cron/package*.json ./services/cron/
COPY services/cron/tsconfig.json ./services/cron/
COPY services/cron/src ./services/cron/src

# Move to the service directory
WORKDIR /app/services/cron

# Install dependencies with npm with retry logic
RUN for i in 1 2 3 4 5; do npm install && break || if [ $i -eq 5 ]; then exit 1; fi; sleep 15; done

# Build the application
RUN npm run build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy built app from builder stage
COPY --from=builder /app/services/cron/dist ./dist
COPY --from=builder /app/services/cron/node_modules ./node_modules
COPY --from=builder /app/services/cron/package*.json ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
  && chown -R node:node /app/logs /app/data

# Switch to non-root user
USER node

EXPOSE 2222

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:2222/health || exit 1

CMD ["node", "dist/index.js"]
