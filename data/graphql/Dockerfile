FROM node:20 AS builder

WORKDIR /app

ARG NODE_ENV
ENV NODE_ENV=$NODE_ENV

COPY data/graphql/src /app

# Final stage
FROM hasura/graphql-engine:v2.15.2

COPY --from=builder /app /app
COPY data/graphql/src/migrations /app/src/migrations/
COPY data/graphql/scripts/run-migrations.sh /app/scripts/

USER root

# Install PostgreSQL client
RUN apt-get update && \
  apt-get install -y curl gnupg2 lsb-release && \
  curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg && \
  echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/postgresql.list && \
  apt-get update && \
  apt-get install -y postgresql-client-15 && \
  rm -rf /var/lib/apt/lists/* && \
  chmod +x /app/scripts/run-migrations.sh

# Add PostgreSQL binaries to PATH
ENV PATH="/usr/lib/postgresql/15/bin:${PATH}"

# Verify installation and paths
RUN find / -name pg_isready 2>/dev/null || true && \
  dpkg -L postgresql-client-15 && \
  ls -la /usr/lib/postgresql/15/bin/ && \
  export PATH="/usr/lib/postgresql/15/bin:${PATH}" && \
  command -v pg_isready

USER hasura

ENTRYPOINT ["/bin/sh", "-c", "/app/scripts/run-migrations.sh && graphql-engine serve"]
