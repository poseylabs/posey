-- Create enum for task priority
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_priority') THEN
        CREATE TYPE task_priority AS ENUM (
            'low',
            'medium',
            'high',
            'urgent'
        );
    END IF;
END $$;

-- Create enum for user task status
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_task_status') THEN
        CREATE TYPE user_task_status AS ENUM (
            'todo',
            'in_progress',
            'blocked',
            'completed',
            'cancelled',
            'deferred'
        );
    END IF;
END $$;

-- Create enum for event recurrence
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_recurrence') THEN
        CREATE TYPE event_recurrence AS ENUM (
            'none',
            'daily',
            'weekly',
            'biweekly',
            'monthly',
            'yearly',
            'custom'
        );
    END IF;
END $$;

-- Create table for user tasks
CREATE TABLE IF NOT EXISTS calendar_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    project_id UUID REFERENCES projects(id),
    title TEXT NOT NULL,
    description TEXT,
    status user_task_status DEFAULT 'todo',
    priority task_priority DEFAULT 'medium',
    due_date TIMESTAMP WITH TIME ZONE,
    reminder_at TIMESTAMP WITH TIME ZONE,
    assigned_to UUID REFERENCES users(id),
    parent_task_id UUID REFERENCES calendar_tasks(id),
    estimated_duration INTERVAL,
    completion_time INTERVAL,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create table for task dependencies
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES calendar_tasks(id) NOT NULL,
    depends_on_task_id UUID REFERENCES calendar_tasks(id) NOT NULL,
    dependency_type TEXT NOT NULL, -- 'blocks', 'relates_to', etc.
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, depends_on_task_id)
);

-- Create table for calendar events
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    project_id UUID REFERENCES projects(id),
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location TEXT,
    is_all_day BOOLEAN DEFAULT false,
    recurrence event_recurrence DEFAULT 'none',
    recurrence_config JSONB DEFAULT '{}',
    reminder_before INTERVAL,
    attendees JSONB DEFAULT '[]',
    conference_link TEXT,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create table for event attendees
CREATE TABLE IF NOT EXISTS event_attendees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES calendar_events(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,
    response_status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'declined', 'tentative'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, user_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_calendar_tasks_user ON calendar_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_tasks_project ON calendar_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_calendar_tasks_status ON calendar_tasks(status);
CREATE INDEX IF NOT EXISTS idx_calendar_tasks_priority ON calendar_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_calendar_tasks_due_date ON calendar_tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_calendar_tasks_assigned ON calendar_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_calendar_tasks_parent ON calendar_tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_calendar_tasks_tags ON calendar_tasks USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_task_dependencies_task ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends ON task_dependencies(depends_on_task_id);

CREATE INDEX IF NOT EXISTS idx_calendar_events_user ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_project ON calendar_events(project_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start ON calendar_events(start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_end ON calendar_events(end_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_recurrence ON calendar_events(recurrence);
CREATE INDEX IF NOT EXISTS idx_calendar_events_tags ON calendar_events USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_event_attendees_event ON event_attendees(event_id);
CREATE INDEX IF NOT EXISTS idx_event_attendees_user ON event_attendees(user_id);
CREATE INDEX IF NOT EXISTS idx_event_attendees_status ON event_attendees(response_status);

-- Drop triggers if they exist
DROP TRIGGER IF EXISTS update_calendar_tasks_updated_at ON calendar_tasks;
DROP TRIGGER IF EXISTS update_calendar_events_updated_at ON calendar_events;
DROP TRIGGER IF EXISTS update_event_attendees_updated_at ON event_attendees;

-- Create triggers (without IF NOT EXISTS)
CREATE TRIGGER update_calendar_tasks_updated_at
    BEFORE UPDATE ON calendar_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_event_attendees_updated_at
    BEFORE UPDATE ON event_attendees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
