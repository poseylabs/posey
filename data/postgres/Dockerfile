FROM postgres:latest

# Install additional dependencies
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY data/postgres/postgresql.conf /etc/postgresql/postgresql.conf

# Copy entire src directory to initialization directory (for first-time setup)
COPY data/postgres/src /docker-entrypoint-initdb.d/

# Copy startup script
COPY data/postgres/scripts/startup.sh /startup.sh
RUN chmod +x /startup.sh

# Copy and setup migration script to run after initialization
COPY data/postgres/scripts/run-migrations.sh /docker-entrypoint-initdb.d/zzz_run_migrations.sh
RUN chmod -R +x /docker-entrypoint-initdb.d/

USER postgres

EXPOSE 3333

# Set the startup script to run after database start
CMD /bin/bash -c "/startup.sh & postgres -c config_file=/etc/postgresql/postgresql.conf"
