ALTER TABLE quiz_dod_users_info
    ADD COLUMN IF NOT EXISTS requested_certificate BOOLEAN NOT NULL DEFAULT FALSE;
