# Build stage
FROM node:20-slim AS builder

# Install necessary build dependencies
RUN apt-get update && apt-get install -y \
  python3 \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy workspace configuration files first
COPY .yarn ./.yarn
COPY .yarnrc.yml .
COPY package.json .
COPY yarn.lock .
COPY .pnp.cjs .
COPY tsconfig.json .

# Copy the service files
COPY services/core/auth ./services/core/auth
COPY packages ./packages

# Enable Yarn Berry
RUN corepack enable && corepack prepare yarn@4.7.0 --activate

# Install dependencies and build
RUN YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn install
RUN yarn workspace @posey.ai/auth build

# Production stage
FROM node:20-slim

# Install PostgreSQL client for pg_isready and migrations
RUN apt-get update && apt-get install -y --no-install-recommends \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy necessary files from builder
COPY --from=builder /app/package.json .
COPY --from=builder /app/.yarnrc.yml .
COPY --from=builder /app/yarn.lock .
COPY --from=builder /app/.yarn ./.yarn
COPY --from=builder /app/.pnp.cjs .
COPY --from=builder /app/services/core/auth/dist ./services/core/auth/dist
COPY --from=builder /app/services/core/auth/package.json ./services/core/auth/
COPY --from=builder /app/services/core/auth/scripts ./services/core/auth/scripts

# Ensure scripts are executable
RUN chmod +x /app/services/core/auth/scripts/start.sh && \
  chmod +x /app/services/core/auth/scripts/run-migrations.sh

# Install production dependencies only
RUN corepack enable && corepack prepare yarn@4.7.0 --activate && \
  YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn workspaces focus @posey.ai/auth --production

# Set environment variables
ENV NODE_ENV=production
ENV NODE_PATH=./services/core/auth/dist

# Expose the port the app runs on
EXPOSE 9999

# Start the application using the start script
CMD ["sh", "services/core/auth/scripts/start.sh"]
