-- Create task_status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
        CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'analyzing', 'paused', 'completed', 'failed', 'cancelled');
    END IF;
END $$;

-- Create background_tasks table
CREATE TABLE IF NOT EXISTS background_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    task_type VARCHAR(50) NOT NULL,
    status task_status DEFAULT 'pending',
    priority task_priority DEFAULT 'medium',
    progress INTEGER DEFAULT 0,
    parameters JSONB DEFAULT '{}'::jsonb,
    result JSONB,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
);

-- Ensure columns exist before indexing
ALTER TABLE background_tasks ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE background_tasks ADD COLUMN IF NOT EXISTS status task_status DEFAULT 'pending';
ALTER TABLE background_tasks ADD COLUMN IF NOT EXISTS next_run_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE background_tasks ADD COLUMN IF NOT EXISTS task_type VARCHAR(50);
-- Add NOT NULL constraints if needed
ALTER TABLE background_tasks ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE background_tasks ALTER COLUMN task_type SET NOT NULL;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_tasks_user ON background_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON background_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_next_run ON background_tasks(next_run_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_tasks_type ON background_tasks(task_type); 
