# Build stage
FROM node:20-slim AS builder

# Set up environment for faster installs
ENV NODE_ENV=production
ENV YARN_NETWORK_TIMEOUT=300000
ENV YARN_ENABLE_TELEMETRY=false

# Install only the minimal dependencies needed
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Set git to use HTTPS instead of SSH for GitHub
RUN git config --global url."https://github.com/".insteadOf git@github.com: \
  && git config --global url."https://github.com/".insteadOf ssh://git@github.com/

WORKDIR /app

# Enable Corepack for Yarn
RUN corepack enable

# Create a dummy root package.json with workspace reference
RUN mkdir -p /app/services/auth

# Copy package.json first to read the package name and Yarn version
COPY package.json /app/services/auth/
COPY tsconfig.json /app/services/auth/
COPY src /app/services/auth/src/

# Extract package name and Yarn version from package.json
RUN PACKAGE_NAME=$(node -p "require('/app/services/auth/package.json').name") && \
  YARN_VERSION=$(node -p "require('/app/services/auth/package.json').packageManager.replace('yarn@', '')") && \
  corepack prepare yarn@$YARN_VERSION --activate

# Create workspace root package.json using the actual package name
RUN PACKAGE_NAME=$(node -p "require('/app/services/auth/package.json').name") && \
  echo "{\"name\":\"root\",\"private\":true,\"workspaces\":{\"packages\":[\"services/auth\"]}}" > /app/package.json

# Create log directories
RUN mkdir -p /app/yarn-logs

# Change to the app root directory
WORKDIR /app

# Try to install dependencies using yarn
RUN mkdir -p /var/log/yarn_attempts && \
  for i in $(seq 1 5); do \
  echo "Yarn install attempt $i" > /var/log/yarn_attempts/attempt_$i.log && \
  PACKAGE_NAME=$(node -p "require('./services/auth/package.json').name") && \
  yarn workspace $PACKAGE_NAME install && break || \
  if [ $i -eq 5 ]; then exit 1; fi; \
  done

# Build the service
RUN PACKAGE_NAME=$(node -p "require('./services/auth/package.json').name") && \
  yarn workspace $PACKAGE_NAME build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install postgres client
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
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
