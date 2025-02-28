-- Create agent_types enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agent_type') THEN
        CREATE TYPE agent_type AS ENUM ('default', 'creative', 'research');
    END IF;
END $$;

-- Create agent_status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agent_status') THEN
        CREATE TYPE agent_status AS ENUM ('active', 'inactive', 'pending', 'disabled');
    END IF;
END $$;

-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type agent_type DEFAULT 'default',
    status agent_status DEFAULT 'active',
    config JSONB DEFAULT '{}'::jsonb,
    provider_id UUID REFERENCES llm_providers(id),
    model_id UUID REFERENCES llm_models(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_agents_provider_id ON agents(provider_id);
CREATE INDEX IF NOT EXISTS idx_agents_model_id ON agents(model_id);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- Drop trigger if exists first
DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;

-- Then create trigger (without IF NOT EXISTS)
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
