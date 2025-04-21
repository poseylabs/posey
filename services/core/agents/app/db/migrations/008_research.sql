-- Create enum for research status
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'research_status') THEN
        CREATE TYPE research_status AS ENUM (
            'new',
            'in_progress',
            'completed',
            'needs_review',
            'archived'
        );
    END IF;
END $$;

-- Create enum for content type
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'content_type') THEN
        CREATE TYPE content_type AS ENUM (
            'text',
            'link',
            'image',
            'audio',
            'video',
            'document',
            'spreadsheet',
            'dataset',
            'code',
            'spreadsheet_data',
            'document_text',
            'extracted_table',
            'converted_file',
            'other'
        );
    END IF;
END $$;

-- Create table for research sessions
CREATE TABLE IF NOT EXISTS research_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    task_id UUID REFERENCES background_tasks(id),
    title TEXT NOT NULL,
    description TEXT,
    query TEXT NOT NULL,
    status research_status NOT NULL DEFAULT 'new',
    auto_tag BOOLEAN DEFAULT true,
    search_parameters JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- Ensure columns exist before indexing
ALTER TABLE research_sessions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE research_sessions ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);
ALTER TABLE research_sessions ADD COLUMN IF NOT EXISTS task_id UUID REFERENCES background_tasks(id);
ALTER TABLE research_sessions ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE research_sessions ALTER COLUMN title SET NOT NULL;
ALTER TABLE research_sessions ALTER COLUMN query SET NOT NULL;
ALTER TABLE research_sessions ALTER COLUMN status SET NOT NULL;

-- Create table for research findings
CREATE TABLE IF NOT EXISTS research_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES research_sessions(id),
    project_id UUID REFERENCES projects(id),
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content_type content_type NOT NULL DEFAULT 'text',
    content JSONB NOT NULL,
    source_url TEXT,
    file_storage_key TEXT,  -- S3 key for stored file
    original_filename TEXT,  -- Original uploaded filename
    mime_type TEXT,         -- File MIME type
    categories TEXT[],
    tags TEXT[],
    confidence_score FLOAT,
    relevance_score FLOAT,
    importance_score INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure columns exist before indexing
ALTER TABLE research_findings ADD COLUMN IF NOT EXISTS session_id UUID REFERENCES research_sessions(id);
ALTER TABLE research_findings ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);
ALTER TABLE research_findings ADD COLUMN IF NOT EXISTS content_type content_type DEFAULT 'text';
ALTER TABLE research_findings ADD COLUMN IF NOT EXISTS categories TEXT[];
ALTER TABLE research_findings ADD COLUMN IF NOT EXISTS tags TEXT[];
ALTER TABLE research_findings ALTER COLUMN session_id SET NOT NULL;
ALTER TABLE research_findings ALTER COLUMN title SET NOT NULL;
ALTER TABLE research_findings ALTER COLUMN summary SET NOT NULL;
ALTER TABLE research_findings ALTER COLUMN content_type SET NOT NULL;
ALTER TABLE research_findings ALTER COLUMN content SET NOT NULL;

-- Create table for user interactions with findings
CREATE TABLE IF NOT EXISTS research_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID NOT NULL REFERENCES research_findings(id),
    user_id UUID NOT NULL REFERENCES users(id),
    interaction_type TEXT NOT NULL, -- 'like', 'dislike', 'favorite', 'hide', 'flag', etc.
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure columns exist before indexing
ALTER TABLE research_interactions ADD COLUMN IF NOT EXISTS finding_id UUID REFERENCES research_findings(id);
ALTER TABLE research_interactions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE research_interactions ADD COLUMN IF NOT EXISTS interaction_type TEXT;
ALTER TABLE research_interactions ALTER COLUMN finding_id SET NOT NULL;
ALTER TABLE research_interactions ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE research_interactions ALTER COLUMN interaction_type SET NOT NULL;

-- Create table for research references
CREATE TABLE IF NOT EXISTS research_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID NOT NULL REFERENCES research_findings(id),
    type TEXT NOT NULL, -- 'webpage', 'academic_paper', 'news_article', 'social_media', etc.
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    summary TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure columns exist before indexing
ALTER TABLE research_references ADD COLUMN IF NOT EXISTS finding_id UUID REFERENCES research_findings(id);
ALTER TABLE research_references ADD COLUMN IF NOT EXISTS type TEXT;
ALTER TABLE research_references ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE research_references ADD COLUMN IF NOT EXISTS url TEXT;
ALTER TABLE research_references ALTER COLUMN finding_id SET NOT NULL;
ALTER TABLE research_references ALTER COLUMN type SET NOT NULL;
ALTER TABLE research_references ALTER COLUMN title SET NOT NULL;
ALTER TABLE research_references ALTER COLUMN url SET NOT NULL;

-- Create table for product ideas
CREATE TABLE IF NOT EXISTS product_ideas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES background_tasks(id),
    user_id UUID REFERENCES users(id) NOT NULL,
    product_name TEXT NOT NULL,
    description TEXT NOT NULL,
    source_url TEXT,
    affiliate_links JSONB DEFAULT '[]',
    category TEXT NOT NULL,
    subcategories TEXT[] DEFAULT '{}',
    status research_status DEFAULT 'new',
    estimated_commission DECIMAL(10,2),
    price_range JSONB DEFAULT '{"min": 0, "max": 0, "currency": "USD"}'::jsonb,
    relevance_score FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_research_sessions_user ON research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_project ON research_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions(status);
CREATE INDEX IF NOT EXISTS idx_research_sessions_task ON research_sessions(task_id);

CREATE INDEX IF NOT EXISTS idx_research_findings_session ON research_findings(session_id);
CREATE INDEX IF NOT EXISTS idx_research_findings_project ON research_findings(project_id);
CREATE INDEX IF NOT EXISTS idx_research_findings_type ON research_findings(content_type);
CREATE INDEX IF NOT EXISTS idx_research_findings_categories ON research_findings USING gin(categories);
CREATE INDEX IF NOT EXISTS idx_research_findings_tags ON research_findings USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_research_interactions_finding ON research_interactions(finding_id);
CREATE INDEX IF NOT EXISTS idx_research_interactions_user ON research_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_research_interactions_type ON research_interactions(interaction_type);

CREATE INDEX IF NOT EXISTS idx_research_references_finding ON research_references(finding_id);
CREATE INDEX IF NOT EXISTS idx_research_references_type ON research_references(type);

CREATE INDEX IF NOT EXISTS idx_product_ideas_task ON product_ideas(task_id);
CREATE INDEX IF NOT EXISTS idx_product_ideas_user ON product_ideas(user_id);
CREATE INDEX IF NOT EXISTS idx_product_ideas_status ON product_ideas(status);
CREATE INDEX IF NOT EXISTS idx_product_ideas_category ON product_ideas(category); 
