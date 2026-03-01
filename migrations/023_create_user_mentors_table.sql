-- 023_create_user_mentors_table.sql
-- Creates the user_mentors table for the GSOM grants section.
-- Stores per-user mentor contacts and a JSONB list of unlocked lesson tags.

CREATE TABLE IF NOT EXISTS user_mentors (
    id               BIGSERIAL PRIMARY KEY,
    user_id          BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    lessons_approved JSONB  NOT NULL DEFAULT '[]'::jsonb,
    mentor_contacts  TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT TIMEZONE('utc', NOW()),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_mentors_user_id UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_mentors_user_id ON user_mentors(user_id);
