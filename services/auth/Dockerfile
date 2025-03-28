# Build stage
FROM node:20-slim AS builder

# Set up environment for faster installs
ENV NODE_ENV=production
ENV YARN_ENABLE_TELEMETRY=false

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

# Setup service directory
WORKDIR /app/services/auth

# Copy service package files
COPY services/auth/package.json ./
COPY services/auth/tsconfig.json ./
COPY services/auth/src ./src/

# Create log directory
RUN mkdir -p /var/log/yarn

# Debug info
RUN echo "Node: $(node --version)" && \
  echo "NPM: $(npm --version)" && \
  echo "Yarn: $(yarn --version)" && \
  echo "Corepack: $(corepack --version)"

# Install using direct approach
RUN yarn install --production
RUN yarn cache clean

# Build the service
RUN yarn build

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
