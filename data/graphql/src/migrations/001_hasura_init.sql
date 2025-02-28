-- Drop existing tables if they exist
DROP SCHEMA IF EXISTS hdb_catalog CASCADE;

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;
