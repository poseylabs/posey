-- Migration to create the invite_codes table
CREATE TABLE IF NOT EXISTS invite_codes (
    code VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    -- Optional: Add columns like 'expires_at', 'uses_remaining', 'created_by' if needed later
    CONSTRAINT code_length_check CHECK (char_length(code) > 0) -- Ensure code is not empty
);

-- Optional: Index for faster lookups if the table grows large
-- CREATE INDEX IF NOT EXISTS idx_invite_codes_created_at ON invite_codes(created_at);

COMMENT ON TABLE invite_codes IS 'Stores single-use invite codes for user registration.';
COMMENT ON COLUMN invite_codes.code IS 'The unique invite code string.';
COMMENT ON COLUMN invite_codes.created_at IS 'Timestamp when the invite code was created.'; 