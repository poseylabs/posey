FROM postgres:latest

# Install additional dependencies
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY postgresql.conf /etc/postgresql/postgresql.conf

# Create postgres role script - must run before any other scripts
RUN echo '#!/bin/bash\necho "Creating postgres role for compatibility"\npsql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF\nDO \$\$\nBEGIN\n  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '\''postgres'\'') THEN\n    CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD '\''postgres'\'';\n  END IF;\nEND\n\$\$;\nEOF' > /docker-entrypoint-initdb.d/01_create_postgres_role.sh && chmod +x /docker-entrypoint-initdb.d/01_create_postgres_role.sh

# Create pocketdb database script - must run after postgres role creation
RUN echo '#!/bin/bash\necho "Creating pocketdb database for user pocketdb"\npsql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE DATABASE pocketdb OWNER pocketdb;"\npsql -U "$POSTGRES_USER" -d "pocketdb" -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"; CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";"' > /docker-entrypoint-initdb.d/02_create_pocketdb.sh && chmod +x /docker-entrypoint-initdb.d/02_create_pocketdb.sh

# Copy entire src directory to initialization directory (for first-time setup)
COPY src /docker-entrypoint-initdb.d/

# Copy startup script
COPY scripts/startup.sh /startup.sh
RUN chmod +x /startup.sh

# Fix the run-migrations.sh script to use localhost
COPY scripts/run-migrations.sh /tmp/run-migrations.sh
RUN sed -i 's/POSTGRES_PORT=.*/PGPORT=3333/g' /tmp/run-migrations.sh && \
    echo '#!/bin/bash\nset -e\n\n# Set localhost connection\nexport PGPORT=3333\nexport PGHOST=localhost\n\n# Wait for PostgreSQL to be ready\nuntil pg_isready -h localhost -p 3333; do\n  echo "Waiting for PostgreSQL to be ready..."\n  sleep 2\ndone\n\n# Initialize Hasura metadata tables\necho "Initializing Hasura metadata tables"\npsql -U "$POSTGRES_USER" -d postgres -h localhost -p 3333 -f /docker-entrypoint-initdb.d/hasura-init.sql\n\n# Run all SQL files in migrations directory in order\nfor f in /docker-entrypoint-initdb.d/migrations/*.sql; do\n  if [ -f "$f" ]; then\n    echo "Running migration $f"\n    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB_POSEY" -h localhost -p 3333 -f "$f"\n  fi\ndone\n\n# Initialize other application databases if needed\necho "All migrations completed successfully!"' > /docker-entrypoint-initdb.d/zzz_run_migrations.sh && \
    chmod +x /docker-entrypoint-initdb.d/zzz_run_migrations.sh

# Create a script to fix PostgreSQL config to listen on all interfaces
RUN echo '#!/bin/bash\necho "Updating PostgreSQL configuration to listen on all interfaces"\n\n# Ensure PostgreSQL listens on all interfaces\nsed -i "s/#listen_addresses = '\''localhost'\''/listen_addresses = '\''*'\''/" /var/lib/postgresql/data/pgdata/postgresql.conf\n\n# Ensure port is set to 3333\nsed -i "s/#port = 5432/port = 3333/" /var/lib/postgresql/data/pgdata/postgresql.conf\n\n# Reload configuration\npg_ctl -D /var/lib/postgresql/data/pgdata reload || true\n' > /docker-entrypoint-initdb.d/02_update_postgresql_config.sh && \
    chmod +x /docker-entrypoint-initdb.d/02_update_postgresql_config.sh

RUN chmod -R +x /docker-entrypoint-initdb.d/

# Set PostgreSQL to listen on port 3333 during initialization
ENV PGPORT=3333

USER postgres

EXPOSE 3333
