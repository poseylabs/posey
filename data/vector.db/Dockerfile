FROM qdrant/qdrant:latest

# Set up environment variables for better npm/yarn behavior
ENV NODE_ENV=production \
  YARN_ENABLE_TELEMETRY=false \
  NPM_CONFIG_REGISTRY=https://registry.npmjs.org/ \
  NPM_CONFIG_STRICT_SSL=false \
  NODE_OPTIONS="--max-old-space-size=4096"

# Install Node.js and Yarn with optimized apt settings
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Enable Corepack for Yarn
RUN corepack enable

# Create directory for config and scripts
WORKDIR /qdrant

# Copy our custom config
COPY data/vector.db/config.yaml config/production.yaml

# Copy initialization scripts and package files
COPY data/vector.db/scripts /qdrant/scripts/
COPY data/vector.db/package.json ./

# Copy root yarn files
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn/ ./.yarn/
COPY .pnp.cjs .pnp.loader.mjs ./

# Configure Yarn network settings to prevent hanging
RUN yarn config set networkTimeout 600000 && \
  yarn config set httpRetry 5 && \
  yarn config set networkConcurrency 4 && \
  npm config set registry https://registry.npmjs.org/

# Install dependencies with optimized settings
RUN yarn install --inline-builds --network-timeout 600000

# Create startup script
COPY data/vector.db/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose ports (REST API, GRPC, and our custom port)
EXPOSE 6333 6334 1111

# Use our custom entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]
