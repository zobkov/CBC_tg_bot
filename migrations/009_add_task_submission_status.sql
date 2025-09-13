-- Добавление колонок для отслеживания статуса отправки заданий
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS task_1_submitted BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS task_2_submitted BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS task_3_submitted BOOLEAN NOT NULL DEFAULT FALSE;

-- Создаем индексы для новых колонок
CREATE INDEX IF NOT EXISTS idx_users_task_1_submitted ON users(task_1_submitted);
CREATE INDEX IF NOT EXISTS idx_users_task_2_submitted ON users(task_2_submitted);
CREATE INDEX IF NOT EXISTS idx_users_task_3_submitted ON users(task_3_submitted);