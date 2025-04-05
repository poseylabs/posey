# Build stage
FROM node:20 AS builder

# Set up environment
ENV NODE_ENV=production
ENV YARN_ENABLE_TELEMETRY=false
ENV NPM_CONFIG_REGISTRY=https://registry.npmjs.org/
ENV NPM_CONFIG_STRICT_SSL=false
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Yarn 4 specific environment variables
ENV YARN_ENABLE_PROGRESS_BARS=true
ENV YARN_VERBOSE=true
ENV YARN_CACHE_FOLDER=/tmp/.yarn-cache
ENV YARN_RC_FILENAME=.yarnrc.yml
ENV YARN_INSTALL_STATE_PATH=/tmp/.yarn-state.gz
ENV YARN_LOG_LEVEL="info"

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

# Copy only the files needed for dependency installation first
# This improves caching and reduces build time
COPY package.json .yarnrc.yml yarn.lock ./
COPY .yarn ./.yarn
COPY services/core/auth/package.json ./services/core/auth/

# Install dependencies - Use full install for build stage
RUN set -x && yarn install --immutable 2>&1 | tee /tmp/yarn-install.log

# Copy remaining files for the build
COPY . .

# Build the service
WORKDIR /app/services/core/auth
RUN set -x && yarn build 2>&1 | tee /tmp/yarn-build.log

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
ENV YARN_ENABLE_TELEMETRY=false
ENV YARN_ENABLE_PROGRESS_BARS=true
ENV YARN_VERBOSE=true

# Copy necessary files from builder
COPY --from=builder /app/services/core/auth/dist ./dist
COPY --from=builder /app/services/core/auth/package.json ./
COPY --from=builder /app/.pnp.cjs /app/.pnp.loader.mjs ./
COPY --from=builder /app/.yarn ./.yarn
COPY --from=builder /app/services/core/auth/scripts ./scripts
COPY --from=builder /app/.yarnrc.yml ./

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs && \
  chown -R node:node /app/logs

# Switch to non-root user
USER node

EXPOSE 9999

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:9999/health || exit 1

# Use the start:container script instead of directly running main.js
CMD ["yarn", "start:container"]
