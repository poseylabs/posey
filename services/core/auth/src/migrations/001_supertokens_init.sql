-- Create apps table first (required for foreign keys)
CREATE TABLE IF NOT EXISTS apps (
    app_id VARCHAR(64) PRIMARY KEY,
    created_at_time BIGINT
);

-- Create tenants table
CREATE TABLE IF NOT EXISTS tenants (
    app_id VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    created_at_time BIGINT,
    PRIMARY KEY (app_id, tenant_id),
    FOREIGN KEY (app_id) REFERENCES apps(app_id) ON DELETE CASCADE
);

-- Insert default app and tenant
INSERT INTO apps (app_id, created_at_time)
VALUES ('public', EXTRACT(EPOCH FROM NOW())::BIGINT)
ON CONFLICT DO NOTHING;

INSERT INTO tenants (app_id, tenant_id, created_at_time)
VALUES ('public', 'public', EXTRACT(EPOCH FROM NOW())::BIGINT)
ON CONFLICT DO NOTHING;
