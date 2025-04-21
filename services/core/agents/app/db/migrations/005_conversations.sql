CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    title TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ensure columns exist before indexing
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);
-- Add NOT NULL constraints if needed
ALTER TABLE conversations ALTER COLUMN user_id SET NOT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);

-- Rename table from 'messages' to 'conversation_messages' to match schema
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    agent_message_id TEXT,
    content JSONB NOT NULL,
    role VARCHAR(50) NOT NULL,
    sender_type VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ensure columns exist before indexing
ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(id);
ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS agent_message_id TEXT;
-- Add NOT NULL constraints if needed
ALTER TABLE conversation_messages ALTER COLUMN conversation_id SET NOT NULL;
ALTER TABLE conversation_messages ALTER COLUMN role SET NOT NULL;
ALTER TABLE conversation_messages ALTER COLUMN content SET NOT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id ON conversation_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_agent_message_id ON conversation_messages(agent_message_id);

-- Drop trigger if exists first
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;

-- Then create trigger (without IF NOT EXISTS)
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
