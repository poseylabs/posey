-- This file is now just for additional setup that needs to happen after the databases are created
-- Database creation is now handled by create-databases.sh

-- You can add database-specific extensions or initial tables here
-- For example:

-- Connect to posey database
\c posey;

-- Create any extensions needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Connect to supertokens database
\c supertokens;

-- Create any extensions needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Output message
\echo 'Database initialization complete'
