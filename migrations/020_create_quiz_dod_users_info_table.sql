CREATE TABLE IF NOT EXISTS quiz_dod_users_info (
    user_id BIGINT PRIMARY KEY,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL
);
