# Build stage
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY services/cron/package*.json ./

# Install dependencies
RUN corepack enable && corepack prepare yarn@4.5.1 --activate && yarn install

# Copy source code and config files
COPY services/cron/tsconfig.json ./
COPY services/cron/src ./src

# Build the application
RUN yarn build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy package files and install production dependencies
COPY --from=builder /app/package*.json ./
RUN corepack enable && corepack prepare yarn@4.5.1 --activate && yarn install --production

# Copy built application
COPY --from=builder /app/dist ./dist

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
  && chown -R node:node /app/logs /app/data

# Switch to non-root user
USER node

EXPOSE 2222

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:2222/health || exit 1

CMD ["node", "dist/index.js"]
