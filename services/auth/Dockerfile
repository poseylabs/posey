# Build stage
FROM node:20-slim AS builder

# Accept build arguments for npm configuration
ARG NPM_CONFIG_REGISTRY=https://registry.npmjs.org/
ARG NPM_CONFIG_FETCH_RETRIES=5
ARG NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=10000
ARG NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=60000
ARG NPM_CONFIG_LOGLEVEL=verbose
ARG NPM_CONFIG_TIMING=true
ARG NPM_CONFIG_LOGS_MAX=10
ARG NPM_CONFIG_LOGS_DIR=/app/services/auth/npm-logs

# Install postgres client and other tools
RUN apt-get update \
  && apt-get install -y postgresql-client curl git \
  && rm -rf /var/lib/apt/lists/*

# Set git to use HTTPS instead of SSH for GitHub
RUN git config --global url."https://github.com/".insteadOf git@github.com: \
  && git config --global url."https://github.com/".insteadOf ssh://git@github.com/

# Set base working directory
WORKDIR /app

# Create npm logs directory
RUN mkdir -p ${NPM_CONFIG_LOGS_DIR}

# Copy only the necessary files for the auth service
COPY services/auth/package*.json ./services/auth/
COPY services/auth/tsconfig.json ./services/auth/
COPY services/auth/src ./services/auth/src

# Move to the auth service directory
WORKDIR /app/services/auth

# Configure npm for better network resilience and logging
RUN npm config set fetch-retries ${NPM_CONFIG_FETCH_RETRIES} \
  && npm config set fetch-retry-mintimeout ${NPM_CONFIG_FETCH_RETRY_MINTIMEOUT} \
  && npm config set fetch-retry-maxtimeout ${NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT} \
  && npm config set registry ${NPM_CONFIG_REGISTRY} \
  && npm config set loglevel ${NPM_CONFIG_LOGLEVEL} \
  && npm config set timing ${NPM_CONFIG_TIMING} \
  && npm config set logs-max ${NPM_CONFIG_LOGS_MAX} \
  && npm config set logs-dir ${NPM_CONFIG_LOGS_DIR}

# Install dependencies with clear cache first to ensure fresh install
RUN npm cache clean --force \
  && for i in 1 2 3 4 5; do \
  echo "Attempt $i: Installing npm dependencies..." && \
  TIMING=1 npm install --no-fund --no-audit --prefer-offline --verbose 2>&1 | tee "${NPM_CONFIG_LOGS_DIR}/npm-install-attempt-${i}.log" && break || \
  if [ $i -eq 5 ]; then \
  echo "All npm install attempts failed. Check logs at ${NPM_CONFIG_LOGS_DIR}/" && \
  cat "${NPM_CONFIG_LOGS_DIR}/npm-install-attempt-${i}.log" && \
  exit 1; \
  fi; \
  echo "Retrying in 15 seconds..." && sleep 15; \
  done

# Build the service
RUN TIMING=1 npm run build --verbose 2>&1 | tee "${NPM_CONFIG_LOGS_DIR}/npm-build.log"

# Production image
FROM node:20-slim

# Install postgres client
RUN apt-get update \
  && apt-get install -y postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Copy built app from builder (correct paths for monorepo structure)
WORKDIR /app
COPY --from=builder /app/services/auth/dist ./dist
COPY --from=builder /app/services/auth/node_modules ./node_modules
COPY --from=builder /app/services/auth/package.json ./
COPY --from=builder /app/services/auth/npm-logs ./npm-logs

# Environment variables
ENV NODE_ENV=production

EXPOSE 9999
CMD ["node", "dist/main.js"]
