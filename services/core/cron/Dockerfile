FROM node:20-slim AS builder

RUN apt-get update && apt-get install -y \
  python3 \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY .yarn ./.yarn/
COPY .yarnrc.yml ./
COPY package.json ./
COPY yarn.lock ./
# COPY .pnp.cjs ./
COPY tsconfig.json ./
COPY services/core/cron ./services/core/cron/
COPY packages ./packages/

RUN corepack enable && corepack prepare yarn@4.7.0 --activate
RUN YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn install
RUN yarn workspace @posey.ai/cron build 

FROM node:20-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/package.json ./
COPY --from=builder /app/.yarnrc.yml ./
COPY --from=builder /app/yarn.lock ./
COPY --from=builder /app/.yarn ./.yarn/
# COPY --from=builder /app/.pnp.cjs ./
COPY --from=builder /app/services/core/cron/package.json ./services/core/cron/

RUN corepack enable && corepack prepare yarn@4.7.0 --activate && \
  YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn workspaces focus @posey.ai/cron

COPY --from=builder /app/services/core/cron/dist ./services/core/cron/dist/
COPY --from=builder /app/services/core/cron/scripts ./services/core/cron/scripts/

RUN chmod +x /app/services/core/cron/scripts/start.sh
RUN mkdir -p /app/logs

ENV NODE_PATH=./services/core/cron/dist 

EXPOSE 2222 

CMD ["sh", "/app/services/core/cron/scripts/start.sh"]

