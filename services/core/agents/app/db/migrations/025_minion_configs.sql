-- Add minion_llm_configs table

CREATE TABLE IF NOT EXISTS minion_llm_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR NOT NULL UNIQUE, -- e.g., 'content_analysis', 'reasoning', 'default', or agent_id
    llm_model_id UUID NOT NULL REFERENCES llm_models(id),
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    top_p FLOAT DEFAULT 0.95,
    frequency_penalty FLOAT DEFAULT 0.0,
    presence_penalty FLOAT DEFAULT 0.0,
    additional_settings JSON,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now() -- Add default now() for updated_at
);

CREATE INDEX IF NOT EXISTS ix_minion_llm_configs_config_key ON minion_llm_configs (config_key);
CREATE INDEX IF NOT EXISTS ix_minion_llm_configs_llm_model_id ON minion_llm_configs (llm_model_id);

-- Insert default configurations for core minions
-- First ensure we have a default model to reference - get the first available model
DO $$
DECLARE
    default_model_id UUID;
BEGIN
    -- Get the first available model ID
    SELECT id INTO default_model_id FROM llm_models LIMIT 1;
    
    -- If no model exists, this will be null and the inserts will fail
    -- which is the desired behavior as we need a valid model
    
    -- Insert default configuration 
    INSERT INTO minion_llm_configs 
        (config_key, llm_model_id, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
    VALUES
        ('default', default_model_id, 0.7, 1000, 0.95, 0.0, 0.0)
    ON CONFLICT (config_key) DO NOTHING;
        
    -- Insert content_analysis minion config
    INSERT INTO minion_llm_configs 
        (config_key, llm_model_id, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
    VALUES
        ('content_analysis', default_model_id, 0.2, 2000, 0.9, 0.0, 0.0)
    ON CONFLICT (config_key) DO NOTHING;
    
    -- Insert memory minion config
    INSERT INTO minion_llm_configs 
        (config_key, llm_model_id, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
    VALUES
        ('memory', default_model_id, 0.3, 2000, 0.9, 0.0, 0.0)
    ON CONFLICT (config_key) DO NOTHING;
        
    -- Insert image_generation minion config
    INSERT INTO minion_llm_configs 
        (config_key, llm_model_id, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
    VALUES
        ('image_generation', default_model_id, 0.8, 1500, 0.95, 0.0, 0.0)
    ON CONFLICT (config_key) DO NOTHING;
        
    -- Insert image_processing minion config
    INSERT INTO minion_llm_configs 
        (config_key, llm_model_id, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
    VALUES
        ('image_processing', default_model_id, 0.3, 2000, 0.9, 0.0, 0.0)
    ON CONFLICT (config_key) DO NOTHING;
        
    -- Insert research minion config
    INSERT INTO minion_llm_configs 
        (config_key, llm_model_id, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
    VALUES
        ('research', default_model_id, 0.4, 3000, 0.9, 0.0, 0.0)
    ON CONFLICT (config_key) DO NOTHING;
        
    -- Insert voyager minion config
    INSERT INTO minion_llm_configs 
        (config_key, llm_model_id, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
    VALUES
        ('voyager', default_model_id, 0.4, 3000, 0.9, 0.0, 0.0)
    ON CONFLICT (config_key) DO NOTHING;
END
$$;