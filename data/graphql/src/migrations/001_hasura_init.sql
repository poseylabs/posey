-- Create extension for UUID generation if not exists
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- If the schema doesn't exist, create it
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_namespace WHERE nspname = 'hdb_catalog') THEN
        CREATE SCHEMA hdb_catalog;
    END IF;
END
$$;

-- Connect as the hasura role if it exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'hasura') THEN
        -- Role exists, note that we can't SET ROLE here because we'd need to be superuser
        -- or have permission to set that role
        RAISE NOTICE 'Using existing hasura role';
    ELSE
        -- Create the hasura role
        CREATE ROLE hasura WITH LOGIN PASSWORD 'hasurapassword';
        GRANT ALL PRIVILEGES ON SCHEMA hdb_catalog TO hasura;
    END IF;
END
$$;

-- Skip the Hasura metadata table creation if it already exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'hdb_catalog' AND table_name = 'hdb_metadata') THEN
        RAISE NOTICE 'Creating Hasura metadata tables';
    ELSE
        RAISE NOTICE 'Hasura metadata tables already exist';
    END IF;
END
$$;
