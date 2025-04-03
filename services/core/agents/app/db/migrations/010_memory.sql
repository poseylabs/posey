CREATE TABLE IF NOT EXISTS memory_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL,
    content TEXT NOT NULL,
    vector_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    importance_score FLOAT DEFAULT 0.5,
    temporal_context TIMESTAMP WITH TIME ZONE,
    categories TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_memory_type CHECK (
        memory_type IN ('fact', 'preference', 'experience', 'skill')
    ),
    CONSTRAINT valid_importance CHECK (
        importance_score >= 0 AND importance_score <= 1
    )
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_memory_agent ON memory_vectors(agent_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_vectors(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_temporal ON memory_vectors(temporal_context);
CREATE INDEX IF NOT EXISTS idx_memory_categories ON memory_vectors USING gin(categories); 
