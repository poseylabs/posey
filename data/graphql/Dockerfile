FROM node:20 as builder
WORKDIR /app

ARG NODE_ENV
ENV NODE_ENV=$NODE_ENV

COPY src /app

FROM hasura/graphql-engine:v2.15.2

COPY --from=builder /app /app
COPY src/migrations /app/src/migrations/
COPY scripts/run-migrations.sh /app/scripts/
COPY scripts/entrypoint.sh /app/scripts/

USER root

# Install PostgreSQL client - modified approach to avoid gpg TTY issues
RUN apt-get update && \
  apt-get install -y curl gnupg2 lsb-release && \
  mkdir -p /usr/share/keyrings && \
  curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
  echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/postgresql.list && \
  apt-get update && \
  apt-get install -y postgresql-client-15 && \
  rm -rf /var/lib/apt/lists/* && \
  chmod +x /app/scripts/run-migrations.sh /app/scripts/entrypoint.sh

# Add PostgreSQL binaries to PATH
ENV PATH="/usr/lib/postgresql/15/bin:${PATH}"

# Verify installation and paths
RUN which pg_isready && \
  dpkg -L postgresql-client-15

USER hasura

# Default port
ENV PORT=4444
EXPOSE 4444

ENTRYPOINT ["/bin/sh", "-c", "/app/scripts/entrypoint.sh"]
