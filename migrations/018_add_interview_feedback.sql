-- Add interview_feedback column to users table
ALTER TABLE users ADD COLUMN interview_feedback TEXT DEFAULT NULL;

-- Add index for performance if needed
CREATE INDEX IF NOT EXISTS idx_users_interview_feedback ON users(interview_feedback) WHERE interview_feedback IS NOT NULL;

-- Comment for documentation
COMMENT ON COLUMN users.interview_feedback IS 'Обратная связь по собеседованию для пользователя';