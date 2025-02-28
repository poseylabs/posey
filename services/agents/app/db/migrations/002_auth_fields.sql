-- Same migration SQL as before
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS username VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE,
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;

ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expiry TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS two_factor_secret TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS inviteCodes (
    id SERIAL PRIMARY KEY,
    code TEXT NOT NULL,
    active BOOLEAN DEFAULT FALSE
);

-- Create sessions table for auth
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- Drop trigger if exists
DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions;

-- Create trigger (without IF NOT EXISTS)
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Add a trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS update_users_updated_at ON users;

-- Create trigger (without IF NOT EXISTS)
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
