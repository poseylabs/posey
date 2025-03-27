# Build stage
FROM node:20-slim AS builder

# Install only the minimal dependencies needed
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set up npm for faster installs
ENV NODE_ENV=production
ENV NPM_CONFIG_LOGLEVEL=error
ENV NPM_CONFIG_FUND=false
ENV NPM_CONFIG_AUDIT=false
ENV NPM_CONFIG_CACHE=/tmp/.npm

# Configure npm for better network resilience
RUN npm config set fetch-retries 5 \
  && npm config set fetch-retry-mintimeout 10000 \
  && npm config set fetch-retry-maxtimeout 60000 \
  && npm config set registry https://registry.npmjs.org/

# Copy package files first for better layer caching
COPY package*.json ./

# Install dependencies using npm ci instead of npm install (faster and more reliable)
RUN npm ci --omit=dev --no-optional

# Copy only the necessary source files
COPY tsconfig.json ./
COPY src ./src

# Build the application
RUN npm run build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install curl for healthcheck (minimal installation)
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production

# Copy only what's needed from the builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
  && chown -R node:node /app/logs /app/data

# Switch to non-root user
USER node

EXPOSE 2222

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:2222/health || exit 1

CMD ["node", "dist/index.js"]
