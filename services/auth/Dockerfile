FROM node:20-slim

# Install postgres client
RUN apt-get update \
  && apt-get install -y postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Add build argument for NODE_ENV
ARG NODE_ENV
ENV NODE_ENV=$NODE_ENV

# Enable Corepack for Yarn 4
RUN corepack enable && corepack prepare yarn@4.5.1 --activate

# Create app directory
WORKDIR /app

# Copy package files first (for better layer caching)
COPY package.json yarn.lock .yarnrc.yml ./
COPY packages/core/package.json ./packages/core/
COPY packages/ui/package.json ./packages/ui/
COPY services/auth/package.json ./services/auth/

# Install dependencies with pruning and offline mode for faster builds
RUN yarn workspaces focus @posey/auth --production

# Now copy the actual code
COPY packages/core ./packages/core/
COPY packages/ui ./packages/ui/
COPY services/auth ./services/auth/

# Copy migrations
COPY services/auth/src/migrations /app/services/auth/src/migrations/
COPY services/auth/scripts/run-migrations.sh /app/services/auth/scripts/
RUN chmod +x /app/services/auth/scripts/run-migrations.sh

# Set working directory to the auth service
WORKDIR /app/services/auth

# Add environment variables
ARG POSTGRES_DSN_POSEY
ARG POSTGRES_USER
ARG POSTGRES_DSN_SUPERTOKENS

ENV POSTGRES_USER=$POSTGRES_USER
ENV POSTGRES_DSN_POSEY=$POSTGRES_DSN_POSEY
ENV POSTGRES_DSN_SUPERTOKENS=$POSTGRES_DSN_SUPERTOKENS

# Add development dependencies if we're not in production
RUN if [ "$NODE_ENV" != "production" ]; then \
  yarn add -D @types/node @types/express @types/cors @types/pg tsconfig-paths; \
  fi

EXPOSE 9999

CMD ["yarn", "start:container"]
