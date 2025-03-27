# Build stage
FROM node:20-slim AS builder

# Set up environment for faster installs
ENV NODE_ENV=production
# Use correct Yarn 4.x configuration format
ENV YARN_ENABLE_TELEMETRY=false
# Note: networkTimeout isn't used directly as an env var in Yarn 4.x

# Install only the minimal dependencies needed
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  && rm -rf /var/lib/apt/lists/*

# Set git to use HTTPS instead of SSH for GitHub
RUN git config --global url."https://github.com/".insteadOf git@github.com: \
  && git config --global url."https://github.com/".insteadOf ssh://git@github.com/

WORKDIR /app

# Enable Corepack for Yarn
RUN corepack enable

# Create Yarn configuration
RUN echo 'httpTimeout: 300000' > /app/.yarnrc.yml

# Create a dummy root package.json with workspace reference
RUN mkdir -p /app/services/cron

# Copy package.json first to read the package name and Yarn version
COPY package.json /app/services/cron/
COPY tsconfig.json /app/services/cron/
COPY src /app/services/cron/src/

# Extract package name and Yarn version from package.json
RUN PACKAGE_NAME=$(node -p "require('/app/services/cron/package.json').name") && \
  YARN_VERSION=$(node -p "require('/app/services/cron/package.json').packageManager.replace('yarn@', '')") && \
  corepack prepare yarn@$YARN_VERSION --activate

# Create workspace root package.json using the actual package name
RUN PACKAGE_NAME=$(node -p "require('/app/services/cron/package.json').name") && \
  echo "{\"name\":\"root\",\"private\":true,\"workspaces\":{\"packages\":[\"services/cron\"]}}" > /app/package.json

# Create log directories
RUN mkdir -p /app/yarn-logs

# Change to the app root directory
WORKDIR /app

# Try to install dependencies using yarn
RUN mkdir -p /var/log/yarn_attempts && \
  for i in $(seq 1 5); do \
  echo "Yarn install attempt $i" > /var/log/yarn_attempts/attempt_$i.log && \
  PACKAGE_NAME=$(node -p "require('./services/cron/package.json').name") && \
  yarn workspace $PACKAGE_NAME install && break || \
  if [ $i -eq 5 ]; then exit 1; fi; \
  done

# Build the service
RUN PACKAGE_NAME=$(node -p "require('./services/cron/package.json').name") && \
  yarn workspace $PACKAGE_NAME build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install curl for healthcheck (minimal installation)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production

# Copy only what's needed from the builder stage
COPY --from=builder /app/services/cron/dist ./dist
COPY --from=builder /app/services/cron/node_modules ./node_modules
COPY --from=builder /app/services/cron/package.json ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
  && chown -R node:node /app/logs /app/data

# Switch to non-root user
USER node

EXPOSE 2222

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:2222/health || exit 1

CMD ["node", "dist/index.js"]
