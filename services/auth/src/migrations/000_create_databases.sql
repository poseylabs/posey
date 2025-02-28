-- Create databases if they don't exist
SELECT 'CREATE DATABASE supertokens'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'supertokens');

SELECT 'CREATE DATABASE posey'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'posey'); 
