# Build stage
FROM node:20-slim AS builder

# Set up environment
ENV NODE_ENV=production \
  YARN_ENABLE_TELEMETRY=false

# Install only the minimal dependencies needed
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  postgresql-client \
  python3 \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Enable Corepack and set up Yarn
RUN corepack enable

# Setup working directory
WORKDIR /app

# Pre-install node-gyp globally
RUN npm install -g node-gyp

# Copy root package files first for better caching
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn/ ./.yarn/
COPY .pnp.cjs .pnp.loader.mjs ./

# Configure Yarn network settings to prevent hanging
RUN yarn config set networkTimeout 300000 && \
  yarn config set httpRetry 3 && \
  yarn config set networkConcurrency 8

# Install dependencies with immutable flag
RUN yarn install --inline-builds --network-timeout 600000

# Copy service-specific files
COPY services/cron/package.json ./services/cron/
COPY services/cron/tsconfig.json ./services/cron/
COPY services/cron/src ./services/cron/src/

# Build the service
WORKDIR /app/services/cron
RUN yarn build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Enable Corepack
RUN corepack enable

ENV NODE_ENV=production

# Copy necessary files from builder
COPY --from=builder /app/services/cron/dist ./dist
COPY --from=builder /app/services/cron/package.json ./
COPY --from=builder /app/.pnp.cjs /app/.pnp.loader.mjs ./
COPY --from=builder /app/.yarn ./.yarn

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs && \
  chown -R node:node /app/logs

# Switch to non-root user
USER node

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:9999/health || exit 1

EXPOSE 9999
CMD ["node", "dist/main.js"]
