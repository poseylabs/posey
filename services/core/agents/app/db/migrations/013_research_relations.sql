-- Add auto_tag to research_sessions
ALTER TABLE research_sessions
ADD COLUMN IF NOT EXISTS auto_tag BOOLEAN DEFAULT false;

-- Add project_id to research_findings
ALTER TABLE research_findings
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);

-- Create index for project lookups
CREATE INDEX IF NOT EXISTS idx_research_findings_project ON research_findings(project_id);

-- Update triggers to maintain project_id consistency
CREATE OR REPLACE FUNCTION update_finding_project_id()
RETURNS TRIGGER AS $$
BEGIN
    -- When a finding is created/updated, get project_id from its session
    IF NEW.session_id IS NOT NULL THEN
        NEW.project_id := (
            SELECT project_id 
            FROM research_sessions 
            WHERE id = NEW.session_id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function to update findings when session project changes
CREATE OR REPLACE FUNCTION update_findings_on_session_project_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only proceed if project_id has changed
    IF OLD.project_id IS DISTINCT FROM NEW.project_id THEN
        -- Update all findings associated with this session
        UPDATE research_findings
        SET project_id = NEW.project_id
        WHERE session_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop triggers if they exist
DROP TRIGGER IF EXISTS trg_research_findings_project_id ON research_findings;
DROP TRIGGER IF EXISTS trg_research_sessions_project_change ON research_sessions;

-- Create triggers
CREATE TRIGGER trg_research_findings_project_id
    BEFORE INSERT OR UPDATE ON research_findings
    FOR EACH ROW
    EXECUTE FUNCTION update_finding_project_id();

CREATE TRIGGER trg_research_sessions_project_change
    AFTER UPDATE ON research_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_findings_on_session_project_change(); 
