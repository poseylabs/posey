-- Add new fields to agents table
ALTER TABLE agents ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS capabilities JSONB DEFAULT '[]'::jsonb;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS type VARCHAR(50);

-- Add IF NOT EXISTS to column additions
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS last_active TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_error JSONB DEFAULT NULL,
ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0;

-- Wrap constraint in DO block
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'valid_error_count'
        AND table_name = 'agents'
    ) THEN
        ALTER TABLE agents ADD CONSTRAINT valid_error_count
        CHECK (error_count >= 0);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_agents_created_by ON agents(created_by);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type); 
