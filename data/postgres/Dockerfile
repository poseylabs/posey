FROM postgres:latest

# Install additional dependencies
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY postgresql.conf /etc/postgresql/postgresql.conf
COPY pg_hba.conf /etc/postgresql/pg_hba.conf

# Copy scripts
COPY scripts/reset_databases.sh /usr/local/bin/reset_databases.sh
COPY scripts/startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/reset_databases.sh /usr/local/bin/startup.sh

# Create postgres role script - must run before any other scripts
COPY scripts/01_create_postgres_role.sh /docker-entrypoint-initdb.d/
COPY scripts/02_create_pocketdb.sh /docker-entrypoint-initdb.d/
COPY scripts/02_update_postgresql_config.sh /docker-entrypoint-initdb.d/
COPY scripts/zzz_run_migrations.sh /docker-entrypoint-initdb.d/

# Copy initialization files
COPY src /docker-entrypoint-initdb.d/

# Set permissions
RUN chmod -R +x /docker-entrypoint-initdb.d/

# Set PostgreSQL to listen on port 3333 during initialization
ENV PGPORT=3333
ENV POSTGRES_HOST_AUTH_METHOD=trust
ENV ENVIRONMENT=development

USER postgres

EXPOSE 3333

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf", "-c", "hba_file=/etc/postgresql/pg_hba.conf"]
