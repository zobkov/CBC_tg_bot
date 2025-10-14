-- Active: 1755689561725@@45.90.217.194@5435@cbc_crew_selection_db_applications
-- Упрощаем систему ролей: удаляем таблицу user_roles и триггеры

-- Удаляем триггер
DROP TRIGGER IF EXISTS trigger_sync_user_roles ON users;

-- Удаляем функцию синхронизации
DROP FUNCTION IF EXISTS sync_user_roles();

-- Удаляем таблицу user_roles
DROP TABLE IF EXISTS user_roles;

-- Убеждаемся, что у всех пользователей есть хотя бы роль guest
UPDATE users 
SET roles = '["guest"]'::jsonb 
WHERE roles IS NULL OR roles = '[]'::jsonb OR jsonb_array_length(roles) = 0;

-- Обновляем роли админов (на всякий случай)
UPDATE users 
SET roles = '["admin"]'::jsonb 
WHERE user_id IN (257026813, 1905792261);

-- Комментарий
COMMENT ON COLUMN users.roles IS 'JSON массив ролей пользователя. Единственное место хранения ролей после упрощения системы';