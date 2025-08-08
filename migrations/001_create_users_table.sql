-- Создание таблицы users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    tz_region VARCHAR(100),
    tz_offset VARCHAR(10),
    longitude DECIMAL(10, 7),
    latitude DECIMAL(10, 7),
    language VARCHAR(5) NOT NULL DEFAULT 'ru',
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_alive BOOLEAN NOT NULL DEFAULT TRUE,
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE
);

-- Создание индексов
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_language ON users(language);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
