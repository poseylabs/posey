# Build stage
FROM node:20-slim AS builder

# Set up environment
ENV NODE_ENV=production \
  YARN_ENABLE_TELEMETRY=false \
  YARN_CACHE_FOLDER=/usr/local/share/.cache/yarn

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

# Enable Corepack and set up Yarn
RUN corepack enable && \
  corepack prepare yarn@stable --activate && \
  yarn set version stable

# Setup working directory
WORKDIR /app

# Copy root package files first for better caching
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn ./.yarn

# Install dependencies with proper caching
RUN --mount=type=cache,target=/usr/local/share/.cache/yarn \
  yarn install --immutable --inline-builds

# Copy service-specific files
COPY services/auth/package.json ./services/auth/
COPY services/auth/tsconfig.json ./services/auth/
COPY services/auth/src ./services/auth/src/

# Build the service
WORKDIR /app/services/auth
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

# Add before CMD
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:9999/health || exit 1

CMD ["node", "dist/main.js"]
