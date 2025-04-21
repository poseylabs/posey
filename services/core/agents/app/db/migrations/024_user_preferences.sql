-- Add preferences column to users table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'preferences'
    ) THEN
        ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Add default preferences for existing users
UPDATE users 
SET preferences = '{
    "llm": {
        "provider": "anthropic",
        "model": "claude-3-5-haiku-latest",
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 0.95,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    "image": {
        "provider": "openai",
        "model": "dalle-3"
    }
}'::jsonb
WHERE preferences IS NULL OR preferences = '{}'::jsonb;
