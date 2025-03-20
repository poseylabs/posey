FROM qdrant/qdrant:latest

# Install Node.js
RUN apt-get update && apt-get install -y \
  curl \
  && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Create directory for config and scripts
WORKDIR /qdrant

# Copy our custom config
COPY config.yaml config/production.yaml

# Copy initialization scripts and package files
COPY scripts /qdrant/scripts/
COPY package*.json ./

# Install dependencies
RUN npm install

# Create startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose ports (REST API, GRPC, and our custom port)
EXPOSE 6333 6334 1111

# Use our custom entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]
