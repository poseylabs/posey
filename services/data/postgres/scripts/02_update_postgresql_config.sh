#!/bin/bash
echo "Updating PostgreSQL configuration to listen on all interfaces"

# Copy the config files
cp /etc/postgresql/postgresql.conf /var/lib/postgresql/data/pgdata/postgresql.conf
cp /etc/postgresql/pg_hba.conf /var/lib/postgresql/data/pgdata/pg_hba.conf

# Set proper permissions
chown postgres:postgres /var/lib/postgresql/data/pgdata/postgresql.conf
chmod 600 /var/lib/postgresql/data/pgdata/postgresql.conf
chown postgres:postgres /var/lib/postgresql/data/pgdata/pg_hba.conf
chmod 600 /var/lib/postgresql/data/pgdata/pg_hba.conf

# Restart PostgreSQL to apply changes
pg_ctl -D /var/lib/postgresql/data/pgdata restart 