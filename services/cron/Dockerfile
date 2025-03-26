# Build stage
FROM node:20-slim as builder

WORKDIR /app

# Enable Corepack for Yarn 4
RUN corepack enable

# Create package.json with packageManager field to avoid Yarn warnings
RUN echo '{"packageManager": "yarn@4.5.1"}' > /app/package.json.temp

# Copy package files
COPY package*.json ./
RUN if [ ! -f "package.json" ]; then mv package.json.temp package.json; else rm package.json.temp; fi

# Prepare Yarn and install dependencies with a timeout
RUN corepack prepare yarn@4.5.1 --activate && \
  yarn config set httpTimeout 600000 && \
  yarn config set networkTimeout 600000 && \
  yarn install --network-timeout 600000 || \
  (echo "Retrying yarn install..." && yarn install --network-timeout 600000)

# Copy source code and config files
COPY tsconfig.json ./
COPY src ./src

# Build the application
RUN yarn build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy built app from builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
  && chown -R node:node /app/logs /app/data

# Switch to non-root user
USER node

EXPOSE 2222

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:2222/health || exit 1

CMD ["node", "dist/index.js"]
