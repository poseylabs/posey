# Build stage
FROM node:20-slim AS builder

# Set up environment for faster installs
ENV NODE_ENV=production
# Use correct Yarn 4.x configuration format
ENV YARN_ENABLE_TELEMETRY=false
ENV YARN_ENABLE_PROGRESS_BARS=false
ENV YARN_ENABLE_GLOBAL_CACHE=false
ENV YARN_VERBOSE=true
ENV DEBUG="yarn*"
# Set Python interpreter for node-gyp
ENV PYTHON=/usr/bin/python3

# Install only the minimal dependencies needed
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  python3 \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Set git to use HTTPS instead of SSH for GitHub
RUN git config --global url."https://github.com/".insteadOf git@github.com: \
  && git config --global url."https://github.com/".insteadOf ssh://git@github.com/

# Enable Corepack for Yarn
RUN corepack enable

# Create Yarn configuration with verbose logging
RUN echo 'httpTimeout: 300000\nlogFilters:\n  - level: info\n    text: "*"\n    code: "*"\nenableGlobalCache: false\nnodeLinker: "node-modules"\nlogLevel: "verbose"\npreferInteractive: false' > /root/.yarnrc.yml

# Setup workspace structure
WORKDIR /app

# Copy root package.json and workspace configuration first
COPY package.json .
COPY yarn.lock .
COPY .yarnrc.yml* ./.yarnrc.yml
COPY .yarn ./.yarn

# Create service directory
RUN mkdir -p /app/services/cron

# Copy cron service package files
COPY services/cron/package.json /app/services/cron/
COPY services/cron/tsconfig.json /app/services/cron/
COPY services/cron/src /app/services/cron/src/

# Create log directories
RUN mkdir -p /app/yarn-logs /var/log/yarn_attempts

# Install dependencies with redirected logging
RUN yarn workspaces focus @posey.ai/cron --production --verbose > /var/log/yarn_attempts/attempt_1.log 2>&1 || \
  (echo "Retrying install..." && yarn workspaces focus @posey.ai/cron --production --verbose > /var/log/yarn_attempts/attempt_2.log 2>&1) || \
  (echo "Final retry..." && yarn workspaces focus @posey.ai/cron --production --verbose > /var/log/yarn_attempts/attempt_3.log 2>&1 && \
  yarn cache clean)

# Build the service (with verbose output)
RUN yarn workspace @posey.ai/cron build --verbose

# Production stage
FROM node:20-slim

WORKDIR /app

# Install curl for healthcheck (minimal installation)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production

# Copy Yarn related files to ensure consistent behavior if needed at runtime
COPY --from=builder /app/.yarn ./.yarn 
COPY --from=builder /app/.yarnrc.yml ./.yarnrc.yml

# Copy only what's needed from the builder stage
COPY --from=builder /app/services/cron/dist ./dist
COPY --from=builder /app/services/cron/node_modules ./node_modules
COPY --from=builder /app/services/cron/package.json ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
  && chown -R node:node /app/logs /app/data /app/.yarn ./.yarnrc.yml

# Switch to non-root user
USER node

EXPOSE 2222

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:2222/health || exit 1

CMD ["node", "dist/index.js"]
