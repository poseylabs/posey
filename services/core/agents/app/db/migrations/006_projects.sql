-- Create enums first
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status') THEN
        CREATE TYPE project_status AS ENUM (
            'new', 'planning', 'in_progress', 'active', 'paused',
            'stale', 'postponed', 'completed', 'abandoned', 'archived'
        );
    END IF;
END $$;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_focus') THEN
        CREATE TYPE project_focus AS ENUM (
            'DEFAULT', 'VISUAL_MEDIA', 'AUDIO_MEDIA', 'CODE',
            'RESEARCH', 'PLANNING', 'WRITING', 'EDUCATION', 'DATA_ANALYSIS'
        );
    END IF;
END $$;

-- Create all tables first
CREATE TABLE IF NOT EXISTS system_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    color TEXT,
    icon TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS user_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT,
    icon TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Ensure user_id column exists before indexing
ALTER TABLE user_tags ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
-- Add NOT NULL constraint if needed (assuming it should always be there)
ALTER TABLE user_tags ALTER COLUMN user_id SET NOT NULL;

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,
    status project_status DEFAULT 'active',
    focus project_focus DEFAULT 'DEFAULT',
    description TEXT,
    start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP WITH TIME ZONE,
    budget DECIMAL(15,2),
    project_colors TEXT[] DEFAULT '{}',
    logo_url TEXT,
    ai_overview TEXT,
    last_overview_update TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, title)
);

-- Ensure key columns exist before indexing or adding constraints
ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS status project_status DEFAULT 'active';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS focus project_focus DEFAULT 'DEFAULT';
-- Add NOT NULL constraints if needed
ALTER TABLE projects ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE projects ALTER COLUMN title SET NOT NULL;
ALTER TABLE projects ALTER COLUMN status SET NOT NULL;
ALTER TABLE projects ALTER COLUMN focus SET NOT NULL;

CREATE TABLE IF NOT EXISTS project_tags (
    project_id UUID REFERENCES projects(id) NOT NULL,
    tag_id UUID NOT NULL,
    is_system_tag BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, tag_id)
);

-- Ensure columns exist before indexing
ALTER TABLE project_tags ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);
ALTER TABLE project_tags ADD COLUMN IF NOT EXISTS tag_id UUID;
ALTER TABLE project_tags ADD COLUMN IF NOT EXISTS is_system_tag BOOLEAN;
-- Add NOT NULL constraints if needed
ALTER TABLE project_tags ALTER COLUMN project_id SET NOT NULL;
ALTER TABLE project_tags ALTER COLUMN tag_id SET NOT NULL;
ALTER TABLE project_tags ALTER COLUMN is_system_tag SET NOT NULL;

CREATE TABLE IF NOT EXISTS project_collaborators (
    project_id UUID REFERENCES projects(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,
    role TEXT NOT NULL,
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id)
);

-- Ensure columns exist before indexing
ALTER TABLE project_collaborators ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);
ALTER TABLE project_collaborators ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE project_collaborators ADD COLUMN IF NOT EXISTS role TEXT;
-- Add NOT NULL constraints if needed
ALTER TABLE project_collaborators ALTER COLUMN project_id SET NOT NULL;
ALTER TABLE project_collaborators ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE project_collaborators ALTER COLUMN role SET NOT NULL;

-- Add foreign key constraints
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_system_tag'
    ) THEN
        ALTER TABLE project_tags
        ADD CONSTRAINT fk_system_tag FOREIGN KEY (tag_id) 
        REFERENCES system_tags(id) 
        DEFERRABLE INITIALLY DEFERRED;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_user_tag'
    ) THEN
        ALTER TABLE project_tags
        ADD CONSTRAINT fk_user_tag FOREIGN KEY (tag_id) 
        REFERENCES user_tags(id) 
        DEFERRABLE INITIALLY DEFERRED;
    END IF;
END $$;

-- Create all functions
CREATE OR REPLACE FUNCTION check_project_tag()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_system_tag THEN
        IF NOT EXISTS (SELECT 1 FROM system_tags WHERE id = NEW.tag_id) THEN
            RAISE EXCEPTION 'Invalid system tag ID';
        END IF;
    ELSE
        IF NOT EXISTS (SELECT 1 FROM user_tags WHERE id = NEW.tag_id) THEN
            RAISE EXCEPTION 'Invalid user tag ID';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop all triggers first
DROP TRIGGER IF EXISTS check_project_tag_trigger ON project_tags;
DROP TRIGGER IF EXISTS update_user_tags_updated_at ON user_tags;
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
DROP TRIGGER IF EXISTS update_project_collaborators_updated_at ON project_collaborators;

-- Create all triggers
CREATE TRIGGER check_project_tag_trigger
    BEFORE INSERT OR UPDATE ON project_tags
    FOR EACH ROW
    EXECUTE FUNCTION check_project_tag();

CREATE TRIGGER update_user_tags_updated_at
    BEFORE UPDATE ON user_tags
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_collaborators_updated_at
    BEFORE UPDATE ON project_collaborators
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_focus ON projects(focus);
CREATE INDEX IF NOT EXISTS idx_user_tags_user ON user_tags(user_id);
CREATE INDEX IF NOT EXISTS idx_project_tags_project ON project_tags(project_id);
CREATE INDEX IF NOT EXISTS idx_project_tags_tag ON project_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_project_collaborators_project ON project_collaborators(project_id);
CREATE INDEX IF NOT EXISTS idx_project_collaborators_user ON project_collaborators(user_id);

-- Insert default data
INSERT INTO system_tags (name, description, category, color, icon) VALUES
('research', 'Research-related content', 'purpose', '#4A90E2', 'search'),
('idea', 'Creative ideas and brainstorming', 'purpose', '#50E3C2', 'lightbulb'),
('task', 'Action items and todos', 'purpose', '#F5A623', 'check-square'),
('important', 'High priority items', 'priority', '#D0021B', 'star'),
('personal', 'Personal projects', 'category', '#9013FE', 'user'),
('business', 'Business-related projects', 'category', '#417505', 'briefcase'),
('shopping', 'Shopping and purchases', 'category', '#7ED321', 'shopping-cart'),
('travel', 'Travel and vacation', 'category', '#BD10E0', 'plane'),
('health', 'Health and wellness', 'category', '#4A90E2', 'heart'),
('finance', 'Financial planning', 'category', '#F8E71C', 'dollar-sign')
ON CONFLICT DO NOTHING; 
