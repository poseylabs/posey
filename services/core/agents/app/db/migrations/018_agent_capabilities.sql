-- Update agents table
ALTER TABLE agents 
    ALTER COLUMN type TYPE agent_type USING type::agent_type,
    ALTER COLUMN status TYPE agent_status USING status::agent_status;

-- Add capabilities column first
ALTER TABLE agents ADD COLUMN IF NOT EXISTS capabilities JSONB DEFAULT '[]'::jsonb;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Add default capabilities
UPDATE agents SET capabilities = '[]'::jsonb WHERE capabilities IS NULL;
UPDATE agents SET metadata = '{}'::jsonb WHERE metadata IS NULL;

-- Add validation function for agent abilities
CREATE OR REPLACE FUNCTION validate_agent_abilities(abilities jsonb)
RETURNS boolean AS $$
BEGIN
    -- Validate each ability is from our known set
    RETURN NOT EXISTS (
        SELECT jsonb_array_elements_text(abilities) AS ability
        WHERE ability NOT IN (
            -- Core
            'conversation', 'task_management', 'planning', 'memory_management',
            -- Code
            'code_generation', 'code_review', 'debugging',
            -- Research
            'research', 'web_search', 'data_analysis', 'document_analysis',
            -- Content Creation
            'text_generation', 'document_creation', 'songwriting',
            -- Visual & Media
            'image_generation', 'image_editing', 'video_generation', 'video_editing',
            -- Other
            'custom'
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Add check constraint for capabilities
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'valid_capabilities'
        AND table_name = 'agents'
    ) THEN
        ALTER TABLE agents ADD CONSTRAINT valid_capabilities
        CHECK (jsonb_array_length(capabilities) >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'validate_agent_abilities_check'
        AND table_name = 'agents'
    ) THEN
        ALTER TABLE agents ADD CONSTRAINT validate_agent_abilities_check
        CHECK (validate_agent_abilities(capabilities));
    END IF;
END $$;

-- Add capabilities tracking
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS training_status jsonb DEFAULT '{}',
ADD COLUMN IF NOT EXISTS last_training timestamp with time zone,
ADD COLUMN IF NOT EXISTS capability_scores jsonb DEFAULT '{}';

-- Add training history
CREATE TABLE IF NOT EXISTS agent_training_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id uuid REFERENCES agents(id) ON DELETE CASCADE,
    capability text NOT NULL,
    training_data jsonb NOT NULL,
    results jsonb NOT NULL,
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp with time zone,
    status text DEFAULT 'pending',
    metrics jsonb DEFAULT '{}'
);

-- Add capability validation
CREATE OR REPLACE FUNCTION validate_agent_capability(
    agent_id uuid,
    capability text
) RETURNS boolean AS $$
DECLARE
    agent_record agents%ROWTYPE;
BEGIN
    SELECT * INTO agent_record FROM agents WHERE id = agent_id;
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    
    -- Check if agent has the capability
    IF NOT capability = ANY(agent_record.capabilities) THEN
        RETURN false;
    END IF;
    
    -- Check capability scores
    IF (agent_record.capability_scores->capability->>'score')::float < 0.7 THEN
        RETURN false;
    END IF;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql; 
