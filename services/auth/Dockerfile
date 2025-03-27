# Build stage
FROM node:20-slim AS builder

# Accept build arguments for npm/yarn configuration
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
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Set git to use HTTPS instead of SSH for GitHub
RUN git config --global url."https://github.com/".insteadOf git@github.com: \
  && git config --global url."https://github.com/".insteadOf ssh://git@github.com/

WORKDIR /app

# Set up environment for faster installs
ENV NODE_ENV=production
ENV NPM_CONFIG_FUND=false
ENV NPM_CONFIG_AUDIT=false
ENV NPM_CONFIG_CACHE=/tmp/.npm

# Enable Corepack for Yarn
RUN corepack enable && \
  corepack prepare yarn@stable --activate

# Create a dummy root package.json with workspace reference
RUN echo '{"name":"root","private":true,"workspaces":{"packages":["services/auth"]}}' > /app/package.json

# Create services directory structure
RUN mkdir -p /app/services/auth

# Copy package files to the service directory
COPY package.json tsconfig.json /app/services/auth/
COPY src /app/services/auth/src/

# Create log directories
RUN mkdir -p /app/yarn-logs

# Change to service directory for next operations
WORKDIR /app/services/auth

# Install dependencies using Yarn without lockfile enforcement
RUN for i in 1 2 3 4 5; do \
  echo "Attempt $i: Installing yarn dependencies..." && \
  cd /app && \
  YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn workspaces focus auth --production 2>&1 | tee "/app/yarn-logs/yarn-install-attempt-${i}.log" && break || \
  if [ $i -eq 5 ]; then \
  echo "All yarn install attempts failed. Check logs at /app/yarn-logs/" && \
  cat "/app/yarn-logs/yarn-install-attempt-${i}.log" && \
  exit 1; \
  fi; \
  echo "Retrying in 15 seconds..." && sleep 15; \
  done

# Build the service
RUN cd /app && yarn workspace auth build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install postgres client
RUN apt-get update && apt-get install -y --no-install-recommends \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production

# Copy only necessary files from builder
COPY --from=builder /app/services/auth/dist ./dist
COPY --from=builder /app/services/auth/node_modules ./node_modules
COPY --from=builder /app/services/auth/package.json ./

# Create necessary directories
RUN mkdir -p /app/logs \
  && chown -R node:node /app/logs

# Switch to non-root user
USER node

EXPOSE 9999
CMD ["node", "dist/main.js"]
