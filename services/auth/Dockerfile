FROM node:20-slim

# Install postgres
RUN apt-get update \
  && apt-get install -y postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Add build argument for NODE_ENV
ARG NODE_ENV
ENV NODE_ENV=$NODE_ENV

# Enable Corepack for Yarn 4
RUN corepack enable && corepack prepare yarn@4.5.1 --activate

# Set working directory to the monorepo root
WORKDIR /app

# Copy monorepo configuration files
COPY package.json .
COPY yarn.lock .
COPY .yarnrc.yml .

# Copy packages directory for workspace dependencies
COPY packages packages/

# Copy the auth service
COPY services/auth services/auth/

# Copy migrations
COPY services/auth/src/migrations /app/services/auth/src/migrations/
COPY services/auth/scripts/run-migrations.sh /app/services/auth/scripts/
RUN chmod +x /app/services/auth/scripts/run-migrations.sh

# Install all dependencies from monorepo root
# NPM_AUTH_TOKEN is only used during build
ARG NPM_AUTH_TOKEN
ARG POSTGRES_DSN_POSEY
ARG POSTGRES_USER

ENV POSTGRES_USER=$POSTGRES_USER
ENV POSTGRES_DSN_POSEY=$POSTGRES_DSN_POSEY

# Add both database connection strings
ENV POSTGRES_DSN_SUPERTOKENS=$POSTGRES_DSN_SUPERTOKENS
ENV POSTGRES_DSN_POSEY=$POSTGRES_DSN_POSEY

# Install dependencies at the root level
RUN yarn install && \
  # Clear NPM_AUTH_TOKEN after install
  unset NPM_AUTH_TOKEN

WORKDIR /app/services/auth

# Configure Yarn to use node-module
RUN yarn config set nodeLinker node-modules
RUN yarn install --mode=update-lockfile

# Make sure @types packages and ts support packages are installed
RUN yarn add -D @types/node @types/express @types/cors @types/pg tsconfig-paths

EXPOSE 9999

CMD ["yarn", "start:container"]
