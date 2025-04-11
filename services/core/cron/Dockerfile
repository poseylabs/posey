FROM node:20-slim AS builder

# Install necessary build dependencies
RUN apt-get update && apt-get install -y \
  python3 \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy workspace configuration files first
COPY .yarnrc.yml ./
COPY package.json ./
COPY yarn.lock ./
COPY tsconfig.json ./

# Copy the service files
COPY services/core/cron ./services/core/cron/
COPY packages ./packages/

# Enable Yarn Berry
RUN corepack enable && corepack prepare yarn@4.7.0 --activate

# Install dependencies and build
RUN YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn install
RUN yarn workspace @posey.ai/cron build 

# Production stage
FROM node:20-slim

# Install PostgreSQL client for pg_isready and migrations
RUN apt-get update && apt-get install -y --no-install-recommends \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV NODE_ENV=production

# Copy necessary files from builder
COPY --from=builder /app/package.json .
COPY --from=builder /app/.yarnrc.yml .
COPY --from=builder /app/yarn.lock .
COPY --from=builder /app/services/core/cron/package.json ./services/core/cron/package.json

RUN corepack enable && corepack prepare yarn@4.7.0 --activate && \
  YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn workspaces focus @posey.ai/cron

COPY --from=builder /app/services/core/cron/dist ./services/core/cron/dist/
COPY --from=builder /app/services/core/cron/scripts ./services/core/cron/scripts/

RUN chmod +x /app/services/core/cron/scripts/start.sh
RUN mkdir -p /app/logs

ENV NODE_PATH=./services/core/cron/dist 

EXPOSE 2222 

CMD ["sh", "/app/services/core/cron/scripts/start.sh"]

