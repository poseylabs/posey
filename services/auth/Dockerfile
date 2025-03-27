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
  postgresql-client \
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
RUN mkdir -p /app/services/auth

# Copy auth service package files
COPY services/auth/package.json /app/services/auth/
COPY services/auth/tsconfig.json /app/services/auth/
COPY services/auth/src /app/services/auth/src/

# Create log directories
RUN mkdir -p /app/yarn-logs /var/log/yarn_attempts

# Install dependencies with redirected logging
RUN yarn workspaces focus @posey.ai/auth --production --verbose > /var/log/yarn_attempts/attempt_1.log 2>&1 || \
  (echo "Retrying install..." && yarn workspaces focus @posey.ai/auth --production --verbose > /var/log/yarn_attempts/attempt_2.log 2>&1) || \
  (echo "Final retry..." && yarn workspaces focus @posey.ai/auth --production --verbose > /var/log/yarn_attempts/attempt_3.log 2>&1 && \
  yarn cache clean)

# Build the service (with verbose output)
RUN yarn workspace @posey.ai/auth build --verbose

# Production stage
FROM node:20-slim

WORKDIR /app

# Install postgres client
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production

# Copy Yarn related files to ensure consistent behavior if needed at runtime
COPY --from=builder /app/.yarn ./.yarn 
COPY --from=builder /app/.yarnrc.yml ./.yarnrc.yml

# Copy only necessary files from builder
COPY --from=builder /app/services/auth/dist ./dist
COPY --from=builder /app/services/auth/node_modules ./node_modules
COPY --from=builder /app/services/auth/package.json ./

# Create necessary directories
RUN mkdir -p /app/logs \
  && chown -R node:node /app/logs /app/.yarn ./.yarnrc.yml

# Switch to non-root user
USER node

EXPOSE 9999
CMD ["node", "dist/main.js"]
