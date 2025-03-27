# Build stage
FROM node:20-slim as builder

WORKDIR /app

# Enable Corepack for Yarn 4
RUN corepack enable

# Create package.json with packageManager field to avoid Yarn warnings
RUN echo '{"packageManager": "yarn@4.5.1"}' > /app/package.json.temp

# Copy entire context to ensure files are available
COPY . /app

# Move to the service directory
WORKDIR /app/services/cron

# Use the temporary package.json if needed
RUN if [ ! -f "package.json" ]; then cp /app/package.json.temp ./package.json; else rm /app/package.json.temp; fi

# Prepare Yarn and install dependencies with optimized settings
RUN corepack prepare yarn@4.5.1 --activate && \
  yarn config set httpTimeout 300000 && \
  yarn config set networkTimeout 300000 && \
  yarn config set networkConcurrency 4 && \
  yarn config set compressionLevel 0 && \
  yarn install --immutable || yarn install --check-cache

# Build the application
RUN yarn build

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
