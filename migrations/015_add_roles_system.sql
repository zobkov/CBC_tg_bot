-- Добавляем столбец roles в таблицу users для хранения JSON-массива ролей
-- Также создаем отдельную таблицу user_roles для более гибкого управления

-- Добавляем в таблицу users столбец для ролей
ALTER TABLE users 
ADD COLUMN roles JSONB DEFAULT '["guest"]'::jsonb NOT NULL;

-- Создаем индекс для эффективного поиска по ролям
CREATE INDEX IF NOT EXISTS idx_users_roles ON users USING GIN (roles);

-- Создаем отдельную таблицу для связи user-role (для будущего развития системы прав)
CREATE TABLE IF NOT EXISTS user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    granted_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    CONSTRAINT check_role_valid CHECK (role IN ('admin', 'staff', 'volunteer', 'guest', 'banned')),
    CONSTRAINT unique_active_user_role UNIQUE (user_id, role) DEFERRABLE INITIALLY DEFERRED
);

-- Индексы для таблицы user_roles
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_roles_granted_by ON user_roles(granted_by);

-- Устанавливаем роль 'guest' по умолчанию для всех существующих пользователей
UPDATE users 
SET roles = '["guest"]'::jsonb 
WHERE roles IS NULL OR roles = '[]'::jsonb;

-- Заполняем таблицу user_roles для существующих пользователей
INSERT INTO user_roles (user_id, role, granted_at, is_active)
SELECT user_id, 'guest', created, TRUE
FROM users
ON CONFLICT (user_id, role) DO NOTHING;

-- Функция для синхронизации ролей между таблицами
CREATE OR REPLACE FUNCTION sync_user_roles() 
RETURNS TRIGGER AS $$
BEGIN
    -- При изменении roles в таблице users - синхронизируем с user_roles
    IF TG_OP = 'UPDATE' AND OLD.roles IS DISTINCT FROM NEW.roles THEN
        -- Деактивируем все старые роли
        UPDATE user_roles 
        SET is_active = FALSE, revoked_at = NOW()
        WHERE user_id = NEW.user_id AND is_active = TRUE;
        
        -- Добавляем новые роли
        INSERT INTO user_roles (user_id, role, granted_at, is_active)
        SELECT NEW.user_id, jsonb_array_elements_text(NEW.roles), NOW(), TRUE
        ON CONFLICT (user_id, role) DO UPDATE 
        SET is_active = TRUE, revoked_at = NULL, granted_at = NOW();
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Создаем триггер для синхронизации
DROP TRIGGER IF EXISTS trigger_sync_user_roles ON users;
CREATE TRIGGER trigger_sync_user_roles
    AFTER UPDATE OF roles ON users
    FOR EACH ROW
    EXECUTE FUNCTION sync_user_roles();

-- Комментарии для документации
COMMENT ON COLUMN users.roles IS 'JSON массив ролей пользователя. Основное хранилище для быстрого доступа';
COMMENT ON TABLE user_roles IS 'Детальная история назначения/отзыва ролей для аудита и расширенного управления';
COMMENT ON COLUMN user_roles.granted_by IS 'ID пользователя, который назначил роль (для аудита)';
COMMENT ON COLUMN user_roles.is_active IS 'Активна ли роль сейчас';
COMMENT ON FUNCTION sync_user_roles() IS 'Синхронизирует изменения ролей между users.roles и user_roles';