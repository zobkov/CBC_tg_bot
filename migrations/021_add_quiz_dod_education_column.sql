ALTER TABLE quiz_dod_users_info
    ADD COLUMN IF NOT EXISTS education TEXT NOT NULL DEFAULT '';
