-- Create enum for file source
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'file_source') THEN
        CREATE TYPE file_source AS ENUM (
            'user_upload',
            'agent_generated',
            'conversion_result',
            'research_artifact',
            'other'
        );
    END IF;
END $$;

-- Create enum for relationship types
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'file_relationship_type') THEN
        CREATE TYPE file_relationship_type AS ENUM (
            'project',
            'conversation',
            'research_session'
        );
    END IF;
END $$;

-- Create table for user files
CREATE TABLE IF NOT EXISTS user_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    source file_source NOT NULL DEFAULT 'user_upload',
    source_task_id UUID REFERENCES background_tasks(id),
    source_agent_id UUID,
    favorite BOOLEAN DEFAULT false,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, storage_key)
);

-- Create table for file relationships (projects, conversations, etc)
CREATE TABLE IF NOT EXISTS file_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES user_files(id) NOT NULL,
    related_type file_relationship_type NOT NULL,
    related_id UUID NOT NULL,
    relationship_context TEXT, -- 'primary_image', 'attachment', 'generated_content', etc.
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_id, related_type, related_id)
);

-- Add foreign key constraints
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_project'
    ) THEN
        ALTER TABLE file_relationships
        ADD CONSTRAINT fk_project FOREIGN KEY (related_id)
        REFERENCES projects(id)
        DEFERRABLE INITIALLY DEFERRED;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_conversation'
    ) THEN
        ALTER TABLE file_relationships
        ADD CONSTRAINT fk_conversation FOREIGN KEY (related_id)
        REFERENCES conversations(id)
        DEFERRABLE INITIALLY DEFERRED;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_research_session'
    ) THEN
        ALTER TABLE file_relationships
        ADD CONSTRAINT fk_research_session FOREIGN KEY (related_id)
        REFERENCES research_sessions(id)
        DEFERRABLE INITIALLY DEFERRED;
    END IF;
END $$;

-- Create trigger function to enforce relationship type constraints
CREATE OR REPLACE FUNCTION check_file_relationship()
RETURNS TRIGGER AS $$
BEGIN
    CASE NEW.related_type
        WHEN 'project' THEN
            IF NOT EXISTS (SELECT 1 FROM projects WHERE id = NEW.related_id) THEN
                RAISE EXCEPTION 'Invalid project ID';
            END IF;
        WHEN 'conversation' THEN
            IF NOT EXISTS (SELECT 1 FROM conversations WHERE id = NEW.related_id) THEN
                RAISE EXCEPTION 'Invalid conversation ID';
            END IF;
        WHEN 'research_session' THEN
            IF NOT EXISTS (SELECT 1 FROM research_sessions WHERE id = NEW.related_id) THEN
                RAISE EXCEPTION 'Invalid research session ID';
            END IF;
    END CASE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop triggers if they exist
DROP TRIGGER IF EXISTS check_file_relationship_trigger ON file_relationships;
DROP TRIGGER IF EXISTS update_user_files_updated_at ON user_files;

-- Create triggers (without IF NOT EXISTS)
CREATE TRIGGER check_file_relationship_trigger
    BEFORE INSERT OR UPDATE ON file_relationships
    FOR EACH ROW
    EXECUTE FUNCTION check_file_relationship();

CREATE TRIGGER update_user_files_updated_at
    BEFORE UPDATE ON user_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create table for file versions (for tracking file conversions/modifications)
CREATE TABLE IF NOT EXISTS file_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_file_id UUID REFERENCES user_files(id) NOT NULL,
    version_number INTEGER NOT NULL,
    storage_key TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    created_by TEXT NOT NULL, -- 'user' or agent_id
    changes_description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(original_file_id, version_number)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_files_user ON user_files(user_id);
CREATE INDEX IF NOT EXISTS idx_user_files_source ON user_files(source);
CREATE INDEX IF NOT EXISTS idx_user_files_tags ON user_files USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_user_files_task ON user_files(source_task_id);
CREATE INDEX IF NOT EXISTS idx_user_files_agent ON user_files(source_agent_id);
CREATE INDEX IF NOT EXISTS idx_file_relationships_file ON file_relationships(file_id);
CREATE INDEX IF NOT EXISTS idx_file_relationships_related ON file_relationships(related_type, related_id);
CREATE INDEX IF NOT EXISTS idx_file_relationships_context ON file_relationships(relationship_context);
CREATE INDEX IF NOT EXISTS idx_file_versions_original ON file_versions(original_file_id); 
