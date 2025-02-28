-- Update integration_configs table
ALTER TABLE integration_configs 
ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL,
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS provider VARCHAR(100) NOT NULL,
ADD COLUMN IF NOT EXISTS base_url TEXT,
ADD COLUMN IF NOT EXISTS version VARCHAR(50),
ADD COLUMN IF NOT EXISTS auth_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS schema JSONB NOT NULL DEFAULT '{}',
ADD COLUMN IF NOT EXISTS agent_permissions TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS last_used TIMESTAMP WITH TIME ZONE;

-- Create index for permissions lookup
CREATE INDEX IF NOT EXISTS idx_integration_permissions ON integration_configs USING GIN (agent_permissions);

-- Add audit timestamps
ALTER TABLE integration_configs
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Drop trigger if exists
DROP TRIGGER IF EXISTS update_integration_configs_updated_at ON integration_configs;

-- Create trigger (without IF NOT EXISTS)
CREATE TRIGGER update_integration_configs_updated_at
    BEFORE UPDATE ON integration_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
