-- Active: 1755689561725@@45.90.217.194@5435@cbc_crew_selection_db_applications
-- Исправляем триггер для корректной работы с ролями

-- Заменяем функцию sync_user_roles для правильной обработки дублирующихся ролей
CREATE OR REPLACE FUNCTION sync_user_roles() 
RETURNS TRIGGER AS $$
DECLARE
    new_role TEXT;
BEGIN
    -- При изменении roles в таблице users - синхронизируем с user_roles
    IF TG_OP = 'UPDATE' AND OLD.roles IS DISTINCT FROM NEW.roles THEN
        -- Деактивируем все старые роли
        UPDATE user_roles 
        SET is_active = FALSE, revoked_at = NOW()
        WHERE user_id = NEW.user_id AND is_active = TRUE;
        
        -- Добавляем новые роли
        FOR new_role IN SELECT jsonb_array_elements_text(NEW.roles) LOOP
            -- Вставляем роль (обновляем существующую или создаем новую)
            INSERT INTO user_roles (user_id, role, granted_at, is_active)
            VALUES (NEW.user_id, new_role, NOW(), TRUE)
            ON CONFLICT (user_id, role) WHERE is_active = TRUE
            DO UPDATE SET 
                granted_at = NOW(),
                is_active = TRUE,
                revoked_at = NULL;
        END LOOP;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Удаляем старый уникальный индекс и создаем новый
DROP INDEX IF EXISTS idx_user_roles_unique_active;

-- Создаем уникальный индекс с именем, который использует constraint
CREATE UNIQUE INDEX IF NOT EXISTS unique_active_user_role 
ON user_roles(user_id, role) WHERE is_active = TRUE;

-- Комментарий к исправлению
COMMENT ON FUNCTION sync_user_roles() IS 'Исправленная синхронизация ролей с поддержкой ON CONFLICT для избежания дублирования';