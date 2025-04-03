-- Update agent_type enum
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'agent_type')
        AND enumlabel = 'creative'
    ) THEN
        ALTER TYPE agent_type ADD VALUE 'creative';
    END IF;
END $$;

-- Update the existing validation function to include new abilities
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
            -- Specialized
            'task_decomposition', 'internet_browsing',
            -- Other
            'custom'
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Add media-related columns to track usage and limits
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS media_generation_config jsonb DEFAULT '{
    "image_generation": {"daily_limit": 50, "used_today": 0, "last_reset": null},
    "video_generation": {"daily_limit": 10, "used_today": 0, "last_reset": null},
    "audio_generation": {"daily_limit": 20, "used_today": 0, "last_reset": null}
}'::jsonb;

-- Function to reset daily media generation counts
CREATE OR REPLACE FUNCTION reset_media_generation_counts()
RETURNS void AS $$
BEGIN
    UPDATE agents
    SET media_generation_config = jsonb_set(
        jsonb_set(
            jsonb_set(
                media_generation_config,
                '{image_generation,used_today}',
                '0'::jsonb
            ),
            '{video_generation,used_today}',
            '0'::jsonb
        ),
        '{audio_generation,used_today}',
        '0'::jsonb
    )
    WHERE media_generation_config IS NOT NULL
    AND (
        media_generation_config->'image_generation'->>'last_reset' IS NULL
        OR (media_generation_config->'image_generation'->>'last_reset')::timestamp < current_date
    );
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically reset counts daily
CREATE OR REPLACE FUNCTION trigger_reset_media_counts()
RETURNS trigger AS $$
BEGIN
    IF NEW.media_generation_config IS NOT NULL THEN
        -- Check if we need to reset counts
        IF (NEW.media_generation_config->'image_generation'->>'last_reset')::timestamp < current_date THEN
            NEW.media_generation_config = jsonb_set(
                NEW.media_generation_config,
                '{image_generation,used_today}',
                '0'::jsonb
            );
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists
DROP TRIGGER IF EXISTS reset_media_counts ON agents;

-- Create trigger (without IF NOT EXISTS)
CREATE TRIGGER reset_media_counts
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION trigger_reset_media_counts();

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_agent_type_creative 
ON agents (type) 
WHERE type = 'creative'; 
