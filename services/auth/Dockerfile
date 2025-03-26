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

# Copy only the files needed for dependencies (improve caching)
COPY package.json yarn.lock .yarnrc.yml ./

# Handle the .yarn directory
RUN mkdir -p ./.yarn

# Copy packages (needed for workspaces)
COPY packages ./packages/

# Copy the auth service
COPY services/auth ./services/auth/

# Install dependencies (only what's needed)
RUN yarn config set httpTimeout 120000 && \
  yarn config set networkConcurrency 1 && \
  yarn workspaces focus @posey.ai/auth --production --verbose

# Set working directory to the auth service
WORKDIR /app/services/auth

# Set up migrations (if they exist)
RUN if [ -f "/app/services/auth/scripts/run-migrations.sh" ]; then \
  chmod +x /app/services/auth/scripts/run-migrations.sh; \
  fi

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
