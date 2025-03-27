# Build stage
FROM node:20-slim AS builder

# Accept build arguments for npm configuration
ARG NPM_CONFIG_REGISTRY=https://registry.npmjs.org/
ARG NPM_CONFIG_FETCH_RETRIES=5
ARG NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=10000
ARG NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=60000
ARG NPM_CONFIG_LOGLEVEL=verbose
ARG NPM_CONFIG_TIMING=true

# Install only the minimal dependencies needed
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  && rm -rf /var/lib/apt/lists/*

# Set git to use HTTPS instead of SSH for GitHub
RUN git config --global url."https://github.com/".insteadOf git@github.com: \
  && git config --global url."https://github.com/".insteadOf ssh://git@github.com/

WORKDIR /app

# Set up npm for faster installs
ENV NODE_ENV=production
ENV NPM_CONFIG_FUND=false
ENV NPM_CONFIG_AUDIT=false
ENV NPM_CONFIG_CACHE=/tmp/.npm

# Configure npm for better network resilience and logging
RUN npm config set fetch-retries ${NPM_CONFIG_FETCH_RETRIES} \
  && npm config set fetch-retry-mintimeout ${NPM_CONFIG_FETCH_RETRY_MINTIMEOUT} \
  && npm config set fetch-retry-maxtimeout ${NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT} \
  && npm config set registry ${NPM_CONFIG_REGISTRY} \
  && npm config set loglevel ${NPM_CONFIG_LOGLEVEL} \
  && npm config set timing ${NPM_CONFIG_TIMING}

# Copy package files first for better layer caching
COPY package*.json ./

# Install dependencies with clear cache first to ensure fresh install
RUN --mount=type=bind,target=/app/npm-logs \
  npm cache clean --force && \
  for i in 1 2 3 4 5; do \
  echo "Attempt $i: Installing npm dependencies..." && \
  TIMING=1 npm ci --no-optional --no-audit --no-fund --prefer-offline --verbose 2>&1 | tee "/app/npm-logs/npm-install-attempt-${i}.log" && break || \
  if [ $i -eq 5 ]; then \
  echo "All npm install attempts failed. Check logs at /app/npm-logs/" && \
  cat "/app/npm-logs/npm-install-attempt-${i}.log" && \
  exit 1; \
  fi; \
  echo "Retrying in 15 seconds..." && sleep 15; \
  done

# Copy only the necessary source files
COPY tsconfig.json ./
COPY src ./src

# Build the service with logging
RUN --mount=type=bind,target=/app/npm-logs \
  TIMING=1 npm run build --verbose 2>&1 | tee "/app/npm-logs/npm-build.log"

# Production stage
FROM node:20-slim

WORKDIR /app

# Install curl for healthcheck (minimal installation)
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production

# Copy only what's needed from the builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
  && chown -R node:node /app/logs /app/data

# Switch to non-root user
USER node

EXPOSE 2222

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:2222/health || exit 1

CMD ["node", "dist/index.js"]
