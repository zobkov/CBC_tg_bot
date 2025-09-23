-- Create task_statistics table to track users accessing TaskSG.main
CREATE TABLE IF NOT EXISTS task_statistics (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    username VARCHAR(255),
    date_first_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)  -- Ensure each user is recorded only once
);

-- Create index for better performance on user_id lookups
CREATE INDEX IF NOT EXISTS idx_task_statistics_user_id ON task_statistics(user_id);

-- Create index for date-based queries
CREATE INDEX IF NOT EXISTS idx_task_statistics_date_first_accessed ON task_statistics(date_first_accessed);