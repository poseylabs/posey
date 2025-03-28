# Build stage
FROM node:20 AS builder

# Set up environment
ENV NODE_ENV=production \
  YARN_ENABLE_TELEMETRY=false \
  NPM_CONFIG_REGISTRY=https://registry.npmjs.org/ \
  NPM_CONFIG_STRICT_SSL=false \
  NODE_OPTIONS="--max-old-space-size=4096"

# Install only the minimal dependencies needed
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  && rm -rf /var/lib/apt/lists/*

# Set git to use HTTPS instead of SSH for GitHub
RUN git config --global url."https://github.com/".insteadOf git@github.com: \
  && git config --global url."https://github.com/".insteadOf ssh://git@github.com/

# Enable Corepack and set up Yarn
RUN corepack enable

# Setup working directory
WORKDIR /app

# Configure Yarn network settings to prevent hanging
RUN yarn config set httpTimeout 600000 && \
  yarn config set httpRetry 5 && \
  yarn config set networkConcurrency 4 && \
  npm config set registry https://registry.npmjs.org/

# Copy the entire monorepo to ensure workspace structure is intact
COPY . .

# Temporarily set NODE_ENV to development to ensure devDependencies are installed
ENV NODE_ENV=development

# Install dependencies focused on cron service with development dependencies
RUN yarn workspaces focus @posey.ai/cron --production=false && \
  yarn cache clean

# Build the service
WORKDIR /app/services/cron
RUN yarn build

# Set NODE_ENV back to production for the remainder of the build
ENV NODE_ENV=production

# Production stage
FROM node:20-slim

WORKDIR /app

# Install postgres client
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

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["node", "dist/main.js"]
