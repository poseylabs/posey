CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    title VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rename table from 'messages' to 'conversation_messages' to match schema
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) NOT NULL,
    content TEXT NOT NULL,
    role VARCHAR(50),
    sender_type VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id ON conversation_messages(conversation_id);

-- Drop trigger if exists first
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;

-- Then create trigger (without IF NOT EXISTS)
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
