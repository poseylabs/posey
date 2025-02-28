# Build stage
FROM node:22-alpine AS builder
WORKDIR /app

# Copy package files and install dependencies
COPY package.json yarn.lock ./
COPY packages packages/
COPY apps/www apps/www/

RUN yarn install

# Build the app
RUN yarn nx build www

# Production stage
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

# Copy necessary files from builder
COPY --from=builder /app/apps/www/.next ./.next
COPY --from=builder /app/apps/www/public ./public
COPY --from=builder /app/apps/www/package.json ./package.json
COPY --from=builder /app/apps/www/next.config.ts ./next.config.ts

# Install production dependencies only
RUN yarn install --production

# Start the app
CMD ["yarn", "start"]