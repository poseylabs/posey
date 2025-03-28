FROM qdrant/qdrant:latest

# Install Node.js and Yarn
RUN apt-get update && apt-get install -y \
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

# Install dependencies
RUN yarn install --inline-builds

# Create startup script
COPY data/vector.db/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose ports (REST API, GRPC, and our custom port)
EXPOSE 6333 6334 1111

# Use our custom entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]
