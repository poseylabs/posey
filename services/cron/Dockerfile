# Build stage
FROM node:20-slim AS builder

# Set up environment
ENV NODE_ENV=production \
  YARN_ENABLE_TELEMETRY=false \
  YARN_CACHE_FOLDER=/usr/local/share/.cache/yarn

# Install minimal dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  postgresql-client \
  python3 \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Set up Yarn properly
RUN corepack enable && \
  corepack prepare yarn@stable --activate && \
  yarn set version stable

# Setup working directory
WORKDIR /app

# Copy package files first for better caching
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn ./.yarn

# Install dependencies with proper caching
RUN --mount=type=cache,target=/usr/local/share/.cache/yarn \
  yarn install --immutable --inline-builds && \
  yarn cache clean

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

ENV NODE_ENV=production

# Copy only necessary files from builder
COPY --from=builder /app/services/cron/dist ./dist
COPY --from=builder /app/services/cron/node_modules ./node_modules
COPY --from=builder /app/services/cron/package.json ./

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
