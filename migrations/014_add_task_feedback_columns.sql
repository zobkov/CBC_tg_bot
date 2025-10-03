-- Migration 014: Add task feedback columns to users table
-- Description: Add feedback columns for task rejections

-- Add feedback columns for tasks
ALTER TABLE users 
ADD COLUMN task_1_feedback TEXT,
ADD COLUMN task_2_feedback TEXT, 
ADD COLUMN task_3_feedback TEXT;

-- Add indexes for faster queries on feedback columns
CREATE INDEX idx_users_task_1_feedback ON users(task_1_feedback) WHERE task_1_feedback IS NOT NULL;
CREATE INDEX idx_users_task_2_feedback ON users(task_2_feedback) WHERE task_2_feedback IS NOT NULL;
CREATE INDEX idx_users_task_3_feedback ON users(task_3_feedback) WHERE task_3_feedback IS NOT NULL;