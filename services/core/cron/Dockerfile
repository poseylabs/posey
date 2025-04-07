# Build stage
FROM node:20-slim AS builder

# Install necessary build dependencies (like auth)
RUN apt-get update && apt-get install -y \
  python3 \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy workspace configuration files first (like auth)
COPY .yarn ./.yarn/
COPY .yarnrc.yml ./
COPY package.json ./
COPY yarn.lock ./
COPY .pnp.cjs ./
COPY tsconfig.json ./

# Copy the service files (adjust path for cron)
COPY services/core/cron ./services/core/cron/
COPY packages ./packages/

# Enable Yarn Berry (like auth)
RUN corepack enable && corepack prepare yarn@4.7.0 --activate

# Install dependencies and build (like auth, install all needed deps)
RUN YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn install
# Run build from root, targeting the cron workspace (like auth)
RUN yarn workspace @posey.ai/cron build 

# Production stage (Seems okay, but let's align WORKDIR and copies)
FROM node:20-slim

# Install PostgreSQL client (assuming cron might need it like auth)
# If not, this can be removed
RUN apt-get update && apt-get install -y --no-install-recommends \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set NODE_ENV before installing dependencies
ENV NODE_ENV=production

# Copy necessary files from builder (aligning with auth)
COPY --from=builder /app/package.json ./
COPY --from=builder /app/.yarnrc.yml ./
COPY --from=builder /app/yarn.lock ./
COPY --from=builder /app/.yarn ./.yarn/
COPY --from=builder /app/.pnp.cjs ./
COPY --from=builder /app/services/core/cron/package.json ./services/core/cron/
# Add copies for any direct workspace dependencies of cron if needed
# COPY --from=builder /app/packages/some-dep/package.json ./packages/some-dep/

# Install production dependencies for the cron workspace ONLY (like auth)
# Run from /app context
RUN corepack enable && corepack prepare yarn@4.7.0 --activate && \
  YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn workspaces focus @posey.ai/cron

# Copy dist AFTER focusing dependencies (aligning with auth)
COPY --from=builder /app/services/core/cron/dist ./services/core/cron/dist/
# Copy any other dependent workspace builds if needed
# COPY --from=builder /app/packages/some-dep/dist ./packages/some-dep/dist/

# Create necessary directories (logs)
RUN mkdir -p /app/logs

# Set environment variables (NODE_ENV is already set)
# Adjust NODE_PATH if necessary based on final structure
ENV NODE_PATH=./services/core/cron/dist 

# Expose the port the app runs on (use the correct port for cron)
EXPOSE 2222 

# HEALTHCHECK (Keep if needed, ensure port matches EXPOSE)
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:2222/health || exit 1

# Start the application (Adjust path)
# Ensure the entry point is correct, maybe use a start script like auth?
# Assuming dist/index.js is the entry point for now
CMD ["node", "services/core/cron/dist/index.js"]

# Consider adding USER node and chown for logs like in auth if applicable
# USER node
# RUN chown -R node:node /app/logs
