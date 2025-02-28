CREATE TABLE IF NOT EXISTS agent_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    feedback_type TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    category TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_feedback_type CHECK (feedback_type IN ('rating', 'text', 'issue')),
    CONSTRAINT valid_feedback_content CHECK (
        (feedback_type = 'rating' AND rating IS NOT NULL) OR
        (feedback_type IN ('text', 'issue') AND feedback_text IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_agent_feedback_agent_id ON agent_feedback(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_type ON agent_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_created_at ON agent_feedback(created_at DESC);
