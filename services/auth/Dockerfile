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

# Copy root package files first for better caching
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn/ ./.yarn/
COPY .pnp.cjs .pnp.loader.mjs ./

# Configure Yarn network settings to prevent hanging
RUN yarn config set networkTimeout 600000 && \
  yarn config set httpRetry 5 && \
  yarn config set networkConcurrency 4 && \
  npm config set registry https://registry.npmjs.org/

# Install dependencies
RUN yarn install --inline-builds --network-timeout 600000

# Copy service-specific files
COPY services/auth/package.json ./services/auth/
COPY services/auth/tsconfig.json ./services/auth/
COPY services/auth/src ./services/auth/src/

# Build the service
WORKDIR /app/services/auth
RUN yarn build

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
COPY --from=builder /app/services/auth/dist ./dist
COPY --from=builder /app/services/auth/package.json ./
COPY --from=builder /app/.pnp.cjs /app/.pnp.loader.mjs ./
COPY --from=builder /app/.yarn ./.yarn

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs && \
  chown -R node:node /app/logs

# Switch to non-root user
USER node

EXPOSE 9999

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:9999/health || exit 1

CMD ["node", "dist/main.js"]
