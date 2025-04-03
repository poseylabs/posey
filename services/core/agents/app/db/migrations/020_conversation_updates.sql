ALTER TABLE conversations ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Add message types and metadata
ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS type VARCHAR(50) DEFAULT 'text';
ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS sender UUID;
ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS sender_type VARCHAR(50);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id ON conversation_messages(conversation_id);

-- Add IF NOT EXISTS to column additions
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS archive_reason TEXT;

-- Add IF NOT EXISTS to index
CREATE INDEX IF NOT EXISTS idx_conversations_archived ON conversations(is_archived);
