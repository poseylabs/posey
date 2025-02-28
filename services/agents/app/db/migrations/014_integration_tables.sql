CREATE TABLE IF NOT EXISTS integration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_type TEXT NOT NULL,
    status TEXT NOT NULL,
    request_data JSONB,
    response_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('success', 'failure', 'pending'))
);

CREATE TABLE IF NOT EXISTS integration_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_type TEXT NOT NULL UNIQUE,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_integration_logs_type ON integration_logs(integration_type);
CREATE INDEX IF NOT EXISTS idx_integration_logs_status ON integration_logs(status);
CREATE INDEX IF NOT EXISTS idx_integration_logs_created_at ON integration_logs(created_at DESC);
