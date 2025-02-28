-- Create base enum types
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status') THEN
        CREATE TYPE project_status AS ENUM (
            'new', 'planning', 'in_progress', 'active', 'paused',
            'stale', 'postponed', 'completed', 'abandoned', 'archived'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_priority') THEN
        CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
        CREATE TYPE task_status AS ENUM (
            'pending', 'in_progress', 'analyzing', 'paused',
            'completed', 'failed', 'cancelled'
        );
    END IF;
END $$;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add seed version tracking
CREATE TABLE IF NOT EXISTS seed_versions (
    version TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
); 

-- Create migrations table to track migration versions
CREATE TABLE IF NOT EXISTS migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
); 
