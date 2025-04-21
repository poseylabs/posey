-- Create feedback_type enum
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedback_type') THEN CREATE TYPE feedback_type AS ENUM ('rating', 'text', 'issue'); END IF; END $$;

-- Create agent_feedback table
CREATE TABLE IF NOT EXISTS agent_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    feedback_type feedback_type NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    category TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_valid_feedback_content CHECK (
        (feedback_type = 'rating' AND rating IS NOT NULL) OR 
        (feedback_type IN ('text', 'issue') AND feedback_text IS NOT NULL)
    )
);

-- Ensure columns exist before indexing
ALTER TABLE agent_feedback ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES agents(id);
ALTER TABLE agent_feedback ADD COLUMN IF NOT EXISTS feedback_type feedback_type;
-- Add NOT NULL constraints if needed
ALTER TABLE agent_feedback ALTER COLUMN agent_id SET NOT NULL;
ALTER TABLE agent_feedback ALTER COLUMN feedback_type SET NOT NULL;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_agent_feedback_agent_id ON agent_feedback(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_type ON agent_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_created_at ON agent_feedback(created_at);
