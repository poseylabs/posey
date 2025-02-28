FROM postgres:latest

# Copy configuration files
COPY data/postgres/postgresql.conf /etc/postgresql/postgresql.conf

# Copy entire src directory to initialization directory
COPY data/postgres/src /docker-entrypoint-initdb.d/

# Copy and setup migration script to run after initialization
COPY data/postgres/scripts/run-migrations.sh /docker-entrypoint-initdb.d/zzz_run_migrations.sh
RUN chmod -R +x /docker-entrypoint-initdb.d/

USER postgres

EXPOSE 3333
ENTRYPOINT ["docker-entrypoint.sh"]

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
