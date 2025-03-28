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

# Enable Yarn through corepack
RUN corepack enable

# Setup working directory
WORKDIR /app

# Copy package files for better caching
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn ./.yarn/
COPY .pnp.cjs .pnp.loader.mjs ./

# Configure Yarn network settings to prevent hanging
RUN yarn config set httpRetry 600000 && \
  yarn config set httpRetry 5 && \
  yarn config set networkConcurrency 4 && \
  npm config set registry https://registry.npmjs.org/

# Copy workspace packages
COPY packages packages/
COPY apps/www apps/www/

# Install dependencies
RUN yarn install --inline-builds --network-timeout 600000

# Build the app
WORKDIR /app/apps/www
RUN yarn build

# Production stage
FROM node:20-slim

WORKDIR /app

ENV NODE_ENV=production \
  PORT=3000 \
  HOSTNAME="0.0.0.0"

# Copy necessary files from builder
COPY --from=builder /app/apps/www/.next/standalone ./
COPY --from=builder /app/apps/www/.next/static ./apps/www/.next/static
COPY --from=builder /app/apps/www/public ./apps/www/public

EXPOSE 3000

CMD ["node", "apps/www/server.js"]