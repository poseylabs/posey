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

# Copy only what's needed for the auth service
COPY package.json ./
COPY yarn.lock ./
COPY .yarnrc.yml ./
COPY .yarn/ ./.yarn/
COPY packages/ ./packages/
COPY services/auth/ ./services/auth/

# Install dependencies (only what's needed)
RUN yarn workspaces focus @posey/auth --production

# Set working directory to the auth service
WORKDIR /app/services/auth

# Set up migrations
RUN chmod +x /app/services/auth/scripts/run-migrations.sh

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
