-- Вставка заявок из CSV файла
-- Файл: 011_insert_csv_applications.sql

-- Сначала добавляем пользователей в таблицу users (если их там еще нет)
INSERT INTO users (user_id, language, is_alive, is_blocked, submission_status)
VALUES 
  -- Получаем user_id из Telegram username, здесь используем временные ID
  -- В реальности нужно будет заменить на реальные Telegram user_id
  (835922894, 'ru', true, false, 'submitted') 
ON CONFLICT (user_id) DO NOTHING;

-- Теперь добавляем заявки в таблицу applications
INSERT INTO applications (
    user_id,
    full_name,
    university,
    phone,
    email,
    telegram_username,
    how_found_kbk,
    previous_department,
    department_1,
    subdepartment_1,
    position_1,
    department_2,
    subdepartment_2,
    position_2,
    department_3,
    subdepartment_3,
    position_3,
    experience,
    motivation,
    created,
    updated
) VALUES 
  (
    835922894, -- user_id для @hlorsson
    'Ким Сабрина Станиславовна',
    NULL,
    NULL,
    NULL,
    'sabrinaseamus',
    NULL, -- Как нашли - пусто в CSV
    NULL, -- Предыдущий отдел - пусто в CSV
    'Выставочный отдел',
    NULL, -- Под-отдел 1 пустой
    'Руководитель отдела',
    'Выставочный отдел', -- Отдел 2 пустой
    NULL, -- Под-отдел 2 пустой
    'Event-менеджер', -- Позиция 2 пустая
    NULL, -- Отдел 3 пустой
    NULL, -- Под-отдел 3 пустой
    NULL, -- Позиция 3 пустая
    NULL, -- Опыт пустой
    NULL, -- Мотивация пустая
    NOW(),
    NOW()
  )
ON CONFLICT (user_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    university = EXCLUDED.university,
    phone = EXCLUDED.phone,
    email = EXCLUDED.email,
    telegram_username = EXCLUDED.telegram_username,
    how_found_kbk = EXCLUDED.how_found_kbk,
    previous_department = EXCLUDED.previous_department,
    department_1 = EXCLUDED.department_1,
    subdepartment_1 = EXCLUDED.subdepartment_1,
    position_1 = EXCLUDED.position_1,
    department_2 = EXCLUDED.department_2,
    subdepartment_2 = EXCLUDED.subdepartment_2,
    position_2 = EXCLUDED.position_2,
    department_3 = EXCLUDED.department_3,
    subdepartment_3 = EXCLUDED.subdepartment_3,
    position_3 = EXCLUDED.position_3,
    experience = EXCLUDED.experience,
    motivation = EXCLUDED.motivation,
    updated = NOW();

-- Теперь добавляем записи в таблицу evaluated_applications
-- На основе колонок "Одобрен 1", "Одобрен 2", "Одобрен 3" из CSV
INSERT INTO evaluated_applications (
    user_id,
    accepted_1,
    accepted_2, 
    accepted_3,
    created,
    updated
) VALUES 
  (
    835922894, -- user_id для @bugassha
    true,  -- Одобрен 1: "Да"
    true,  -- Одобрен 2: "Да"  
    false,  -- Одобрен 3: "Да"
    NOW(),
    NOW()
  )
ON CONFLICT (user_id) DO UPDATE SET
    accepted_1 = EXCLUDED.accepted_1,
    accepted_2 = EXCLUDED.accepted_2,
    accepted_3 = EXCLUDED.accepted_3,
    updated = NOW();

-- Обновляем submission_status в таблице users на основе статуса заявки
UPDATE users 
SET submission_status = (
    CASE 
        WHEN applications.status = 'submitted' THEN 'submitted'
        ELSE 'not_submitted'
    END
),
updated = NOW()
FROM applications 
WHERE users.user_id = applications.user_id;