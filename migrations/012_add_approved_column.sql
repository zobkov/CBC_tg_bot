-- Add approved column to users table for interview scheduling
ALTER TABLE users ADD COLUMN IF NOT EXISTS approved INTEGER NOT NULL DEFAULT 0;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_users_approved ON users(approved);

-- Add constraint to ensure approved is between 0-3
ALTER TABLE users ADD CONSTRAINT check_approved_range CHECK (approved >= 0 AND approved <= 3);