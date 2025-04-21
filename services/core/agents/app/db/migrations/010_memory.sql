CREATE TABLE IF NOT EXISTS memory_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) NOT NULL,
    content TEXT NOT NULL,
    vector_id TEXT NOT NULL,
    memory_type TEXT NOT NULL CHECK (memory_type IN ('fact', 'preference', 'experience', 'skill')),
    importance_score FLOAT CHECK (importance_score >= 0 AND importance_score <= 1),
    temporal_context TIMESTAMPTZ,
    categories TEXT[],
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure columns exist before indexing
ALTER TABLE memory_vectors ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES agents(id);
ALTER TABLE memory_vectors ADD COLUMN IF NOT EXISTS memory_type TEXT CHECK (memory_type IN ('fact', 'preference', 'experience', 'skill'));
ALTER TABLE memory_vectors ADD COLUMN IF NOT EXISTS temporal_context TIMESTAMPTZ;
ALTER TABLE memory_vectors ADD COLUMN IF NOT EXISTS categories TEXT[];
-- Add NOT NULL constraints if needed
ALTER TABLE memory_vectors ALTER COLUMN agent_id SET NOT NULL;
ALTER TABLE memory_vectors ALTER COLUMN content SET NOT NULL;
ALTER TABLE memory_vectors ALTER COLUMN vector_id SET NOT NULL;
ALTER TABLE memory_vectors ALTER COLUMN memory_type SET NOT NULL;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_memory_agent ON memory_vectors(agent_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_vectors(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_temporal ON memory_vectors(temporal_context);
CREATE INDEX IF NOT EXISTS idx_memory_categories ON memory_vectors USING gin(categories); 
