-- Add project_id to conversations for project conversations
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);

-- Create index for project_id lookups
CREATE INDEX IF NOT EXISTS idx_conversations_project ON conversations(project_id);

-- Conditionally add unique constraint
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'unique_conversation_project' AND conrelid = 'conversations'::regclass) THEN
        ALTER TABLE conversations ADD CONSTRAINT unique_conversation_project UNIQUE (id, project_id);
    END IF;
END $$; 
