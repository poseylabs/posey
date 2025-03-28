# Build stage
FROM node:22-alpine AS builder
WORKDIR /app

# Enable Yarn through corepack
RUN corepack enable

# Pre-install node-gyp globally
RUN npm install -g node-gyp

# Copy package files for better caching
COPY package.json yarn.lock .yarnrc.yml ./
COPY .yarn ./.yarn/
COPY .pnp.cjs .pnp.loader.mjs ./

# Copy workspace packages
COPY packages packages/
COPY apps/www apps/www/

# Configure Yarn network settings to prevent hanging
RUN yarn config set networkTimeout 300000 && \
  yarn config set httpRetry 3 && \
  yarn config set networkConcurrency 8

# Install dependencies with immutable flag
RUN yarn install --inline-builds --network-timeout 600000

# Build the app
RUN yarn nx build www

# Production stage
FROM node:22-alpine AS runner
WORKDIR /app

# Enable Yarn through corepack
RUN corepack enable

ENV NODE_ENV production

# Copy PnP files from builder
COPY --from=builder /app/.pnp.cjs /app/.pnp.loader.mjs ./
COPY --from=builder /app/.yarn ./.yarn

# Copy necessary files from builder
COPY --from=builder /app/apps/www/.next ./.next
COPY --from=builder /app/apps/www/public ./public
COPY --from=builder /app/apps/www/package.json ./package.json
COPY --from=builder /app/apps/www/next.config.ts ./next.config.ts

# Start the app
CMD ["yarn", "start"]