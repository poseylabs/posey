-- Connect to default postgres database first
\c postgres;

-- Terminate existing connections to databases we want to drop
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname IN ('posey', 'supertokens')
AND pid <> pg_backend_pid();

-- Drop existing databases if they exist
-- TODO: Remove this after initial database schema is finalized
DROP DATABASE IF EXISTS posey;
DROP DATABASE IF EXISTS supertokens;

CREATE DATABASE posey;
CREATE DATABASE supertokens;
