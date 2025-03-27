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
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Set git to use HTTPS instead of SSH for GitHub
RUN git config --global url."https://github.com/".insteadOf git@github.com: \
  && git config --global url."https://github.com/".insteadOf ssh://git@github.com/

# Enable Corepack for Yarn
RUN corepack enable

# Create Yarn configuration
RUN echo 'httpTimeout: 300000' > /root/.yarnrc.yml

# Setup workspace structure
WORKDIR /app

# Copy root package.json and workspace configuration first
COPY package.json .
COPY .yarnrc.yml* ./.yarnrc.yml

# Create service directory
RUN mkdir -p /app/services/auth

# Copy auth service package files
COPY services/auth/package.json /app/services/auth/
COPY services/auth/tsconfig.json /app/services/auth/
COPY services/auth/src /app/services/auth/src/

# Install dependencies for this service only
RUN yarn workspaces focus @posey.ai/auth --production || \
  (echo "Retrying install..." && yarn workspaces focus @posey.ai/auth --production) || \
  (echo "Final retry..." && yarn workspaces focus @posey.ai/auth --production)

# Build the service
RUN yarn workspace @posey.ai/auth build

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
