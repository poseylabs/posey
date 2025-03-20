#!/bin/bash
echo "Creating postgres role for compatibility"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOF
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'postgres') THEN
    CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'postgres';
  END IF;
END
\$\$;
EOF 