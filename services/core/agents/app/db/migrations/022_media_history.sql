-- Create media_generation_history table first
CREATE TABLE IF NOT EXISTS media_generation_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    agent_id uuid REFERENCES agents(id),
    media_type text NOT NULL,
    prompt text NOT NULL,
    result_url text,
    metadata jsonb DEFAULT '{}',
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_media_history_agent ON media_generation_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_media_history_user ON media_generation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_media_history_type ON media_generation_history(media_type);

-- Add user_id column to media_generation_history table
ALTER TABLE media_generation_history
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id); 
